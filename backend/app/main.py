from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .data import dataset_preview, table_fields
from .grader import grade_submission, score_conclusion
from .storage import get_progress_map, init_db, list_wrong_notes, mark_wrong_note_reviewed, record_attempt, wrong_note_count
from .tasks import DAY_META, get_task, list_tasks, SQL_STARTER, TASK_BY_ID


class RunRequest(BaseModel):
    code: str


class ConclusionRequest(BaseModel):
    text: str


app = FastAPI(title="本地 SQL/Python 机考训练器")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db()


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/days")
def days() -> dict[str, object]:
    progress = get_progress_map()
    tasks = list_tasks()
    task_meta = {task.id: task.public_dict() for task in tasks}
    day_payload = []
    for day_num, meta in DAY_META.items():
        day_tasks = [task for task in tasks if task.day == day_num]
        completed = sum(1 for task in day_tasks if progress.get(task.id, {}).get("passed") == 1)
        day_payload.append(
            {
                "day": day_num,
                "title": meta["title"],
                "focus": meta["focus"],
                "task_count": len(day_tasks),
                "completed_count": completed,
                "tasks": [
                    {
                        "id": task.id,
                        "title": task.title,
                        "mode": task.mode,
                        "timebox_minutes": task.timebox_minutes,
                        "tier": task_meta[task.id]["tier"],
                        "difficulty": task_meta[task.id]["difficulty"],
                        "tags": task_meta[task.id]["tags"],
                        "is_generated": task_meta[task.id]["is_generated"],
                        "passed": progress.get(task.id, {}).get("passed") == 1,
                        "attempts": progress.get(task.id, {}).get("attempts", 0),
                    }
                    for task in day_tasks
                ],
            }
        )
    total_completed = sum(1 for task in tasks if progress.get(task.id, {}).get("passed") == 1)
    return {
        "days": day_payload,
        "summary": {
            "task_count": len(tasks),
            "completed_count": total_completed,
            "sprint_count": sum(1 for meta in task_meta.values() if meta["tier"] == "sprint"),
            "recommended_count": sum(1 for meta in task_meta.values() if meta["tier"] in {"sprint", "core"}),
            "drill_count": sum(1 for meta in task_meta.values() if meta["tier"] == "drill"),
            "wrong_note_count": wrong_note_count(),
        },
    }


@app.get("/api/tasks/{task_id}")
def task_detail(task_id: str) -> dict[str, object]:
    if task_id not in TASK_BY_ID:
        raise HTTPException(status_code=404, detail="Task not found")
    task = get_task(task_id)
    fields = {table: table_fields(table) for table in task.datasets}
    return {
        "task": task.public_dict(),
        "starter_code": task.starter_code or SQL_STARTER,
        "solution": task.solution,
        "field_dictionary": fields,
        "sample_data": dataset_preview(list(task.datasets)),
    }


@app.post("/api/tasks/{task_id}/run")
def run_task(task_id: str, payload: RunRequest) -> dict[str, object]:
    if task_id not in TASK_BY_ID:
        raise HTTPException(status_code=404, detail="Task not found")
    task = get_task(task_id)
    result = grade_submission(task, payload.code)
    record_attempt(
        task_id=task.id,
        mode=task.mode,
        code=payload.code,
        passed=bool(result["passed"]),
        error_type=result.get("error_type"),
        feedback=str(result.get("feedback", "")),
    )
    return result


@app.post("/api/tasks/{task_id}/conclusion")
def submit_conclusion(task_id: str, payload: ConclusionRequest) -> dict[str, object]:
    if task_id not in TASK_BY_ID:
        raise HTTPException(status_code=404, detail="Task not found")
    return score_conclusion(payload.text)


@app.get("/api/wrong-notes")
def wrong_notes() -> dict[str, object]:
    notes = []
    for note in list_wrong_notes():
        task = TASK_BY_ID.get(note["task_id"])
        note["task_title"] = task.title if task else note["task_id"]
        note["day"] = task.day if task else None
        note["mode"] = task.mode if task else None
        notes.append(note)
    return {"notes": notes}


@app.post("/api/wrong-notes/{note_id}/mark-reviewed")
def mark_reviewed(note_id: int) -> dict[str, object]:
    if not mark_wrong_note_reviewed(note_id):
        raise HTTPException(status_code=404, detail="Wrong note not found")
    return {"ok": True}
