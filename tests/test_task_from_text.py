from datetime import date

import anthropic
import httpx


def test_create_task_from_text(client, fake_llm_service):
    fake_llm_service.extracted = {
        "title": "Buy milk",
        "description": "Get it from the store",
        "due_date": "2026-07-03",
        "priority": "high",
    }

    response = client.post("/tasks/from-text", json={"text": "buy milk tomorrow, it's urgent"})

    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "Buy milk"
    assert body["description"] == "Get it from the store"
    assert body["due_date"] == "2026-07-03"
    assert body["priority"] == "high"


def test_create_task_from_text_passes_reference_date(client, fake_llm_service):
    fake_llm_service.extracted = {"title": "Something"}

    client.post("/tasks/from-text", json={"text": "do something tomorrow"})

    assert fake_llm_service.last_call["reference_date"] == date.today().isoformat()
    assert fake_llm_service.last_call["text"] == "do something tomorrow"


def test_create_task_from_text_defaults_priority_when_absent(client, fake_llm_service):
    fake_llm_service.extracted = {"title": "No priority given"}

    response = client.post("/tasks/from-text", json={"text": "no priority mentioned"})

    assert response.status_code == 201
    assert response.json()["priority"] == "medium"


def test_create_task_from_text_no_due_date(client, fake_llm_service):
    fake_llm_service.extracted = {"title": "No date"}

    response = client.post("/tasks/from-text", json={"text": "no date mentioned"})

    assert response.status_code == 201
    assert response.json()["due_date"] is None


def test_create_task_from_text_blank_text_returns_422(client):
    response = client.post("/tasks/from-text", json={"text": ""})
    assert response.status_code == 422


def test_create_task_from_text_missing_title_returns_422(client, fake_llm_service):
    fake_llm_service.extracted = {}

    response = client.post("/tasks/from-text", json={"text": "gibberish extraction"})

    assert response.status_code == 422


def test_create_task_from_text_llm_failure_returns_502(client, fake_llm_service):
    def raise_error(text, *, reference_date):
        raise anthropic.APIConnectionError(
            message="boom", request=httpx.Request("POST", "https://api.anthropic.com/v1/messages")
        )

    fake_llm_service.extract_task = raise_error

    response = client.post("/tasks/from-text", json={"text": "whatever"})

    assert response.status_code == 502
