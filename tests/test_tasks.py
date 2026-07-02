import time


def test_create_and_get_task(client):
    response = client.post("/tasks/", json={"title": "Write tests", "description": "Cover CRUD"})
    assert response.status_code == 201
    created = response.json()
    assert created["title"] == "Write tests"
    assert created["completed"] is False
    assert created["created_at"] == created["updated_at"]

    response = client.get(f"/tasks/{created['id']}")
    assert response.status_code == 200
    assert response.json()["title"] == "Write tests"


def test_list_tasks(client):
    client.post("/tasks/", json={"title": "A"})
    client.post("/tasks/", json={"title": "B"})

    response = client.get("/tasks/")
    assert response.status_code == 200
    body = response.json()
    assert body["total_count"] == 2
    assert len(body["items"]) == 2
    assert body["limit"] == 20
    assert body["offset"] == 0


def test_list_tasks_filter_by_status(client):
    client.post("/tasks/", json={"title": "A", "status": "pending"})
    client.post("/tasks/", json={"title": "B", "status": "completed"})

    response = client.get("/tasks/", params={"status": "completed"})
    assert response.status_code == 200
    body = response.json()
    assert body["total_count"] == 1
    assert body["items"][0]["title"] == "B"


def test_list_tasks_filter_by_priority(client):
    client.post("/tasks/", json={"title": "A", "priority": "low"})
    client.post("/tasks/", json={"title": "B", "priority": "high"})

    response = client.get("/tasks/", params={"priority": "high"})
    assert response.status_code == 200
    body = response.json()
    assert body["total_count"] == 1
    assert body["items"][0]["title"] == "B"


def test_list_tasks_filter_by_tags(client):
    client.post("/tasks/", json={"title": "A", "tags": ["urgent", "work"]})
    client.post("/tasks/", json={"title": "B", "tags": ["personal"]})
    client.post("/tasks/", json={"title": "C", "tags": []})

    response = client.get("/tasks/", params={"tags": ["urgent"]})
    assert response.status_code == 200
    body = response.json()
    assert body["total_count"] == 1
    assert body["items"][0]["title"] == "A"


def test_list_tasks_sorting(client):
    client.post("/tasks/", json={"title": "Charlie"})
    client.post("/tasks/", json={"title": "Alice"})
    client.post("/tasks/", json={"title": "Bob"})

    response = client.get("/tasks/", params={"sort_by": "title", "sort_order": "asc"})
    assert response.status_code == 200
    titles = [item["title"] for item in response.json()["items"]]
    assert titles == ["Alice", "Bob", "Charlie"]


def test_list_tasks_pagination(client):
    for i in range(5):
        client.post("/tasks/", json={"title": f"Task {i}", "priority": "medium"})

    response = client.get("/tasks/", params={"limit": 2, "offset": 0, "sort_by": "title", "sort_order": "asc"})
    body = response.json()
    assert body["total_count"] == 5
    assert body["limit"] == 2
    assert body["offset"] == 0
    assert [item["title"] for item in body["items"]] == ["Task 0", "Task 1"]

    response = client.get("/tasks/", params={"limit": 2, "offset": 2, "sort_by": "title", "sort_order": "asc"})
    body = response.json()
    assert [item["title"] for item in body["items"]] == ["Task 2", "Task 3"]


def test_get_task_not_found(client):
    response = client.get("/tasks/999")
    assert response.status_code == 404


def test_create_task_blank_title_returns_422(client):
    response = client.post("/tasks/", json={"title": "   "})
    assert response.status_code == 422


def test_create_task_missing_title_returns_422(client):
    response = client.post("/tasks/", json={"description": "no title"})
    assert response.status_code == 422


def test_update_task(client):
    created = client.post("/tasks/", json={"title": "Original"}).json()

    time.sleep(1.1)
    response = client.put(f"/tasks/{created['id']}", json={"title": "Updated", "completed": True})
    assert response.status_code == 200
    updated = response.json()
    assert updated["title"] == "Updated"
    assert updated["completed"] is True
    assert updated["updated_at"] > updated["created_at"]


def test_update_task_not_found(client):
    response = client.put("/tasks/999", json={"title": "Updated"})
    assert response.status_code == 404


def test_update_task_blank_title_returns_422(client):
    created = client.post("/tasks/", json={"title": "Original"}).json()

    response = client.put(f"/tasks/{created['id']}", json={"title": "   "})
    assert response.status_code == 422


def test_delete_task(client):
    created = client.post("/tasks/", json={"title": "To delete"}).json()

    response = client.delete(f"/tasks/{created['id']}")
    assert response.status_code == 204

    response = client.get(f"/tasks/{created['id']}")
    assert response.status_code == 404


def test_delete_task_not_found(client):
    response = client.delete("/tasks/999")
    assert response.status_code == 404
