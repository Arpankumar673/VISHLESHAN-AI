from uuid import uuid4
import pytest
from fastapi.testclient import TestClient
from app.core.security import AuthenticatedUser, get_current_user
from app.main import app

client = TestClient(app)
test_user_id = uuid4()


@pytest.fixture(autouse=True)
def override_auth_dependency():
    app.dependency_overrides[get_current_user] = lambda: AuthenticatedUser(
        id=test_user_id, email="test@example.com", role="authenticated"
    )
    yield
    app.dependency_overrides.pop(get_current_user, None)


def test_ask_api_empty_question_rejected():
    payload = {
        "company_id": str(uuid4()),
        "question": "   ",
        "company_name": "Test Co",
    }
    res = client.post("/api/v1/ask", json=payload)
    assert res.status_code in (400, 422)


def test_ask_api_valid_question():
    company_id = "16586585-8032-476c-9ea1-a3db7f1b70f9"
    payload = {
        "company_id": company_id,
        "question": "Is the recruitment process verified?",
        "company_name": "HackIndia",
    }
    res = client.post("/api/v1/ask", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "data" in data
    ask_data = data["data"]
    assert ask_data["company_id"] == company_id
    assert "answer" in ask_data
    assert isinstance(ask_data["citations"], list)
