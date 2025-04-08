import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_full_report():
    response = client.post(
        "/api/v1/full-report",
        json={
            "db_option": "khamis",
            "start_date": "2024-01-01T00:00:00",
            "end_date": "2024-12-31T23:59:59"
        }
    )
    assert response.status_code == 200
    assert "pdf_bytes" in response.json()
    assert len(response.json()["payment_report"]) > 0