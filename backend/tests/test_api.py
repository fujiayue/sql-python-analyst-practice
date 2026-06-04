from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_days_api() -> None:
    response = client.get("/api/days")
    assert response.status_code == 200
    payload = response.json()
    assert payload["summary"]["task_count"] >= 150
    assert len(payload["days"]) == 7


def test_task_detail_api() -> None:
    response = client.get("/api/tasks/d1_sql_02_month_volume")
    assert response.status_code == 200
    payload = response.json()
    assert payload["task"]["mode"] == "sql"
    assert "tickets" in payload["sample_data"]
