from src.cache import TASK_LIST_CACHE_PREFIX


def test_list_tasks_is_cached(client, redis_client):
    client.post("/tasks/", json={"title": "A"})

    response = client.get("/tasks/")
    assert response.status_code == 200
    assert response.json()["total_count"] == 1

    keys = list(redis_client.scan_iter(match=f"{TASK_LIST_CACHE_PREFIX}*"))
    assert len(keys) == 1

    # Insert a task directly so the DB and cache disagree; a cache hit should
    # still return the stale cached count, proving the response was served
    # from cache rather than recomputed.
    client.post("/tasks/", json={"title": "B"})
    redis_client.set(keys[0], response.text)

    cached_response = client.get("/tasks/")
    assert cached_response.json()["total_count"] == 1


def test_cache_invalidated_on_create(client, redis_client):
    client.get("/tasks/")
    assert len(list(redis_client.scan_iter(match=f"{TASK_LIST_CACHE_PREFIX}*"))) == 1

    client.post("/tasks/", json={"title": "New task"})

    assert list(redis_client.scan_iter(match=f"{TASK_LIST_CACHE_PREFIX}*")) == []

    response = client.get("/tasks/")
    assert response.json()["total_count"] == 1


def test_cache_invalidated_on_update(client, redis_client):
    created = client.post("/tasks/", json={"title": "Original"}).json()
    client.get("/tasks/")
    assert len(list(redis_client.scan_iter(match=f"{TASK_LIST_CACHE_PREFIX}*"))) == 1

    client.put(f"/tasks/{created['id']}", json={"title": "Renamed"})

    assert list(redis_client.scan_iter(match=f"{TASK_LIST_CACHE_PREFIX}*")) == []

    response = client.get("/tasks/")
    assert response.json()["items"][0]["title"] == "Renamed"


def test_cache_invalidated_on_delete(client, redis_client):
    created = client.post("/tasks/", json={"title": "Doomed"}).json()
    client.get("/tasks/")
    assert len(list(redis_client.scan_iter(match=f"{TASK_LIST_CACHE_PREFIX}*"))) == 1

    client.delete(f"/tasks/{created['id']}")

    assert list(redis_client.scan_iter(match=f"{TASK_LIST_CACHE_PREFIX}*")) == []

    response = client.get("/tasks/")
    assert response.json()["total_count"] == 0


def test_cache_invalidated_on_dependency_change(client, redis_client):
    a = client.post("/tasks/", json={"title": "A"}).json()
    b = client.post("/tasks/", json={"title": "B"}).json()
    client.get("/tasks/")
    assert len(list(redis_client.scan_iter(match=f"{TASK_LIST_CACHE_PREFIX}*"))) == 1

    client.post(f"/tasks/{a['id']}/dependencies", json={"depends_on_id": b["id"]})
    assert list(redis_client.scan_iter(match=f"{TASK_LIST_CACHE_PREFIX}*")) == []

    response = client.get("/tasks/")
    task_a = next(item for item in response.json()["items"] if item["id"] == a["id"])
    assert task_a["dependency_ids"] == [b["id"]]

    client.get("/tasks/")
    assert len(list(redis_client.scan_iter(match=f"{TASK_LIST_CACHE_PREFIX}*"))) == 1

    client.delete(f"/tasks/{a['id']}/dependencies/{b['id']}")
    assert list(redis_client.scan_iter(match=f"{TASK_LIST_CACHE_PREFIX}*")) == []


def test_cache_keys_vary_by_query_params(client, redis_client):
    client.post("/tasks/", json={"title": "A", "priority": "high"})
    client.post("/tasks/", json={"title": "B", "priority": "low"})

    client.get("/tasks/", params={"priority": "high"})
    client.get("/tasks/", params={"priority": "low"})

    assert len(list(redis_client.scan_iter(match=f"{TASK_LIST_CACHE_PREFIX}*"))) == 2
