import anthropic
import httpx


def _create_task(client, title="Fix login bug", description="Users can't sign in"):
    return client.post("/tasks/", json={"title": title, "description": description}).json()


def test_get_suggested_tags(client, fake_llm_service):
    task = _create_task(client)
    fake_llm_service.suggested_tags = ["bug", "auth", "urgent"]

    response = client.get(f"/tasks/{task['id']}/suggested-tags")

    assert response.status_code == 200
    assert response.json()["tags"] == ["bug", "auth", "urgent"]


def test_get_suggested_tags_passes_title_and_description(client, fake_llm_service):
    task = _create_task(client, title="Fix login bug", description="Users can't sign in")

    client.get(f"/tasks/{task['id']}/suggested-tags")

    assert fake_llm_service.last_call == {
        "title": "Fix login bug",
        "description": "Users can't sign in",
    }


def test_get_suggested_tags_does_not_modify_task(client, fake_llm_service):
    task = _create_task(client)
    fake_llm_service.suggested_tags = ["bug", "auth"]

    client.get(f"/tasks/{task['id']}/suggested-tags")

    response = client.get(f"/tasks/{task['id']}")
    assert response.json()["tags"] == []


def test_get_suggested_tags_not_found(client):
    response = client.get("/tasks/999/suggested-tags")
    assert response.status_code == 404


def test_get_suggested_tags_llm_failure_returns_502(client, fake_llm_service):
    task = _create_task(client)

    def raise_error(title, description=None):
        raise anthropic.APIConnectionError(
            message="boom", request=httpx.Request("POST", "https://api.anthropic.com/v1/messages")
        )

    fake_llm_service.suggest_tags = raise_error

    response = client.get(f"/tasks/{task['id']}/suggested-tags")

    assert response.status_code == 502


def test_get_recommended_priority(client, fake_llm_service):
    task = _create_task(client)
    fake_llm_service.recommended_priority = "high"

    response = client.get(f"/tasks/{task['id']}/recommended-priority")

    assert response.status_code == 200
    assert response.json()["priority"] == "high"


def test_get_recommended_priority_does_not_modify_task(client, fake_llm_service):
    task = _create_task(client)
    fake_llm_service.recommended_priority = "high"

    client.get(f"/tasks/{task['id']}/recommended-priority")

    response = client.get(f"/tasks/{task['id']}")
    assert response.json()["priority"] == "medium"


def test_get_recommended_priority_not_found(client):
    response = client.get("/tasks/999/recommended-priority")
    assert response.status_code == 404


def test_get_recommended_priority_llm_failure_returns_502(client, fake_llm_service):
    task = _create_task(client)

    def raise_error(title, description=None):
        raise anthropic.APIConnectionError(
            message="boom", request=httpx.Request("POST", "https://api.anthropic.com/v1/messages")
        )

    fake_llm_service.recommend_priority = raise_error

    response = client.get(f"/tasks/{task['id']}/recommended-priority")

    assert response.status_code == 502
