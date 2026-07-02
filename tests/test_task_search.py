def test_create_task_upserts_embedding(client, fake_embedding_service):
    response = client.post(
        "/tasks/", json={"title": "Fix login bug", "description": "Users can't sign in"}
    )
    task_id = str(response.json()["id"])

    assert fake_embedding_service.upserted[task_id] == "Fix login bug\nUsers can't sign in"


def test_create_task_without_description_embeds_title_only(client, fake_embedding_service):
    response = client.post("/tasks/", json={"title": "Fix login bug"})
    task_id = str(response.json()["id"])

    assert fake_embedding_service.upserted[task_id] == "Fix login bug"


def test_update_task_re_upserts_embedding(client, fake_embedding_service):
    created = client.post("/tasks/", json={"title": "Original title"}).json()
    task_id = str(created["id"])
    assert fake_embedding_service.upserted[task_id] == "Original title"

    client.put(f"/tasks/{task_id}", json={"title": "Updated title", "description": "New details"})

    assert fake_embedding_service.upserted[task_id] == "Updated title\nNew details"


def test_delete_task_removes_embedding(client, fake_embedding_service):
    created = client.post("/tasks/", json={"title": "Doomed task"}).json()
    task_id = str(created["id"])

    client.delete(f"/tasks/{task_id}")

    assert task_id in fake_embedding_service.deleted


def test_create_task_from_text_upserts_embedding(client, fake_llm_service, fake_embedding_service):
    fake_llm_service.extracted = {"title": "Buy milk"}

    response = client.post("/tasks/from-text", json={"text": "buy milk"})
    task_id = str(response.json()["id"])

    assert fake_embedding_service.upserted[task_id] == "Buy milk"


def test_search_returns_tasks_in_ranked_order(client, fake_embedding_service):
    a = client.post("/tasks/", json={"title": "A"}).json()
    b = client.post("/tasks/", json={"title": "B"}).json()
    c = client.post("/tasks/", json={"title": "C"}).json()

    fake_embedding_service.search_results = [str(c["id"]), str(a["id"])]

    response = client.get("/tasks/search", params={"q": "something relevant"})

    assert response.status_code == 200
    body = response.json()
    assert [item["id"] for item in body] == [c["id"], a["id"]]
    assert b["id"] not in [item["id"] for item in body]


def test_search_passes_query_and_limit(client, fake_embedding_service):
    client.get("/tasks/search", params={"q": "urgent bug", "limit": 3})

    assert fake_embedding_service.last_search == {"query_text": "urgent bug", "n_results": 3}


def test_search_defaults_limit(client, fake_embedding_service):
    client.get("/tasks/search", params={"q": "urgent bug"})

    assert fake_embedding_service.last_search["n_results"] == 10


def test_search_skips_ids_no_longer_in_db(client, fake_embedding_service):
    fake_embedding_service.search_results = ["999"]

    response = client.get("/tasks/search", params={"q": "ghost task"})

    assert response.status_code == 200
    assert response.json() == []


def test_search_requires_query_param(client):
    response = client.get("/tasks/search")
    assert response.status_code == 422


def test_search_blank_query_returns_422(client):
    response = client.get("/tasks/search", params={"q": ""})
    assert response.status_code == 422
