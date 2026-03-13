from fastapi.testclient import TestClient

from tests.integration.api.test_movements import bootstrap_containers


def test_list_clients_returns_clients(client: TestClient):
    # Seed a client by doing a rich issue; this creates a client "alice"
    bootstrap_containers(client)
    r = client.post(
        "/api/movements/issue",
        json={
            "name": "Alice",
            "primary_category_id": "containers",
            "container_type_id": "white",
            "quantity": 1,
            "content_type_ids": [],
            "note": None,
        },
    )
    assert r.status_code == 201

    # Now /api/clients should list that client
    r = client.get("/api/clients")
    assert r.status_code == 200
    data = r.json()
    assert isinstance(data, list)
    assert any(c["name"] == "alice" for c in data)
