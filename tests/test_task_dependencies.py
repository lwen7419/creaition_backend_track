def _create_task(client, title, **kwargs):
    return client.post("/tasks/", json={"title": title, **kwargs}).json()


def test_add_and_read_dependency(client):
    a = _create_task(client, "A")
    b = _create_task(client, "B")

    response = client.post(f"/tasks/{a['id']}/dependencies", json={"depends_on_id": b["id"]})
    assert response.status_code == 201
    assert response.json()["dependency_ids"] == [b["id"]]


def test_add_dependency_task_not_found(client):
    a = _create_task(client, "A")

    response = client.post(f"/tasks/{a['id']}/dependencies", json={"depends_on_id": 999})
    assert response.status_code == 404


def test_add_self_dependency_returns_400(client):
    a = _create_task(client, "A")

    response = client.post(f"/tasks/{a['id']}/dependencies", json={"depends_on_id": a["id"]})
    assert response.status_code == 400


def test_add_duplicate_dependency_returns_409(client):
    a = _create_task(client, "A")
    b = _create_task(client, "B")
    client.post(f"/tasks/{a['id']}/dependencies", json={"depends_on_id": b["id"]})

    response = client.post(f"/tasks/{a['id']}/dependencies", json={"depends_on_id": b["id"]})
    assert response.status_code == 409


def test_add_circular_dependency_returns_400(client):
    a = _create_task(client, "A")
    b = _create_task(client, "B")
    c = _create_task(client, "C")

    # A depends on B, B depends on C
    assert client.post(f"/tasks/{a['id']}/dependencies", json={"depends_on_id": b["id"]}).status_code == 201
    assert client.post(f"/tasks/{b['id']}/dependencies", json={"depends_on_id": c["id"]}).status_code == 201

    # C -> A would close the cycle A -> B -> C -> A
    response = client.post(f"/tasks/{c['id']}/dependencies", json={"depends_on_id": a["id"]})
    assert response.status_code == 400


def test_remove_dependency(client):
    a = _create_task(client, "A")
    b = _create_task(client, "B")
    client.post(f"/tasks/{a['id']}/dependencies", json={"depends_on_id": b["id"]})

    response = client.delete(f"/tasks/{a['id']}/dependencies/{b['id']}")
    assert response.status_code == 204

    response = client.get(f"/tasks/{a['id']}")
    assert response.json()["dependency_ids"] == []


def test_remove_dependency_not_found(client):
    a = _create_task(client, "A")
    b = _create_task(client, "B")

    response = client.delete(f"/tasks/{a['id']}/dependencies/{b['id']}")
    assert response.status_code == 404


def test_dependency_tree_recursive(client):
    a = _create_task(client, "A")
    b = _create_task(client, "B")
    c = _create_task(client, "C")

    # A depends on B, B depends on C
    client.post(f"/tasks/{a['id']}/dependencies", json={"depends_on_id": b["id"]})
    client.post(f"/tasks/{b['id']}/dependencies", json={"depends_on_id": c["id"]})

    response = client.get(f"/tasks/{a['id']}/dependencies/tree")
    assert response.status_code == 200
    tree = response.json()
    assert tree["id"] == a["id"]
    assert len(tree["dependencies"]) == 1
    assert tree["dependencies"][0]["id"] == b["id"]
    assert len(tree["dependencies"][0]["dependencies"]) == 1
    assert tree["dependencies"][0]["dependencies"][0]["id"] == c["id"]


def test_dependency_tree_not_found(client):
    response = client.get("/tasks/999/dependencies/tree")
    assert response.status_code == 404


def test_complete_task_blocked_by_incomplete_dependency(client):
    a = _create_task(client, "A")
    b = _create_task(client, "B", status="pending")
    client.post(f"/tasks/{a['id']}/dependencies", json={"depends_on_id": b["id"]})

    response = client.put(f"/tasks/{a['id']}", json={"status": "completed"})
    assert response.status_code == 409


def test_complete_task_blocked_via_completed_flag(client):
    a = _create_task(client, "A")
    b = _create_task(client, "B", status="pending")
    client.post(f"/tasks/{a['id']}/dependencies", json={"depends_on_id": b["id"]})

    response = client.put(f"/tasks/{a['id']}", json={"completed": True})
    assert response.status_code == 409


def test_complete_task_allowed_when_dependencies_completed(client):
    a = _create_task(client, "A")
    b = _create_task(client, "B", status="completed")
    client.post(f"/tasks/{a['id']}/dependencies", json={"depends_on_id": b["id"]})

    response = client.put(f"/tasks/{a['id']}", json={"status": "completed"})
    assert response.status_code == 200
    assert response.json()["status"] == "completed"


def test_complete_task_allowed_with_no_dependencies(client):
    a = _create_task(client, "A")

    response = client.put(f"/tasks/{a['id']}", json={"status": "completed"})
    assert response.status_code == 200
