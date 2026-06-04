from backend.app.grader import grade_python, grade_sql, score_conclusion
from backend.app.tasks import get_task


def test_sql_solution_passes() -> None:
    task = get_task("d1_sql_01_team_volume")
    result = grade_sql(task, task.solution)
    assert result["passed"] is True


def test_sql_column_mismatch_fails() -> None:
    task = get_task("d1_sql_01_team_volume")
    result = grade_sql(task, "SELECT team, COUNT(*) AS cnt FROM tickets GROUP BY team ORDER BY team")
    assert result["passed"] is False
    assert result["error_type"] == "column_mismatch"


def test_python_solution_passes() -> None:
    task = get_task("d3_py_02_team_metrics")
    result = grade_python(task, task.solution)
    assert result["passed"] is True


def test_conclusion_scoring() -> None:
    result = score_conclusion("发现 AP 团队 SLA 下降到 68%，可能由于高优先级工单集中，建议进一步查看返工率。")
    assert result["passed"] is True
    assert result["score"] >= 3

