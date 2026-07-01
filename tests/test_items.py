def test_create_and_get_item(client):
    response = client.post("/items/", json={"name": "Widget", "description": "A test widget"})
    assert response.status_code == 201
    created = response.json()
    assert created["name"] == "Widget"

    response = client.get(f"/items/{created['id']}")
    assert response.status_code == 200
    assert response.json()["name"] == "Widget"


def test_get_item_not_found(client):
    response = client.get("/items/999")
    assert response.status_code == 404


def test_list_items(client):
    client.post("/items/", json={"name": "A"})
    client.post("/items/", json={"name": "B"})

    response = client.get("/items/")
    assert response.status_code == 200
    assert len(response.json()) == 2
