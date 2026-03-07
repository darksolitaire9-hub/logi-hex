"""
Integration tests for rich movement endpoints.

These tests cover the full HTTP → facade → SQLite path for:
- /api/tracking-categories  (bootstrap)
- /api/tracking-items       (bootstrap)
- /api/movements/issue      (rich OUT transaction)
- /api/movements/receive    (rich IN transaction)
- /api/summary              (balance after movements)
- /api/issue                (guard: old simple flow still works)

Each test is self-contained: it bootstraps its own required data
(tracking categories, items, container types) so tests can run in
any order without depending on shared state.
"""

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def bootstrap_containers(client):
    """
    Creates the 'containers' tracking category and 'white' tracking item.

    Required before any /api/movements/* call, since the domain validates
    that the primary category exists and has enforce_returns=True.
    """
    client.post(
        "/api/tracking-categories",
        json={"id": "containers", "name": "Containers", "enforce_returns": True},
    )
    client.post(
        "/api/tracking-items",
        json={"id": "white", "label": "White Box", "category_id": "containers"},
    )


# ---------------------------------------------------------------------------
# Bootstrap tests
# ---------------------------------------------------------------------------


def test_create_tracking_category_returns_correct_shape(client):
    """
    POST /api/tracking-categories should return 201
    with the created category fields including enforce_returns.
    """
    r = client.post(
        "/api/tracking-categories",
        json={"id": "containers", "name": "Containers", "enforce_returns": True},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["id"] == "containers"
    assert data["name"] == "Containers"
    assert data["enforce_returns"] is True


def test_create_tracking_item_returns_correct_shape(client):
    """
    POST /api/tracking-items should return 201
    with the created item fields including category_id.
    """
    bootstrap_containers(client)

    r = client.post(
        "/api/tracking-items",
        json={"id": "round", "label": "Round Box", "category_id": "containers"},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["id"] == "round"
    assert data["label"] == "Round Box"
    assert data["category_id"] == "containers"


# ---------------------------------------------------------------------------
# Rich movements tests
# ---------------------------------------------------------------------------


def test_rich_issue_returns_correct_shape(client):
    """
    POST /api/movements/issue with content_type_ids and note should:
    - Return 201
    - Include direction=OUT
    - Echo primary_items with correct tracking_item_id and quantity
    - Echo secondary_items (content tags)
    - Echo the note
    - Include a transaction_id
    """
    bootstrap_containers(client)

    r = client.post(
        "/api/movements/issue",
        json={
            "name": "Alice",
            "container_type_id": "white",
            "quantity": 3,
            "content_type_ids": ["veg", "no_onion"],
            "note": "Lunch delivery",
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert "transaction_id" in data
    assert data["client_name"] == "alice"
    assert data["direction"] == "OUT"
    assert data["notes"] == "Lunch delivery"
    assert len(data["primary_items"]) == 1
    assert data["primary_items"][0]["tracking_item_id"] == "white"
    assert data["primary_items"][0]["quantity"] == 3
    assert set(data["secondary_items"]) == {"veg", "no_onion"}


def test_rich_receive_returns_correct_shape(client):
    """
    POST /api/movements/receive should:
    - Return 201
    - Include direction=IN
    - Echo primary_items with correct quantity
    - Echo note
    - Only allowed if prior issue exists (enforce_returns enforced by domain)
    """
    bootstrap_containers(client)
    # Issue first so balance allows the return
    client.post(
        "/api/movements/issue",
        json={
            "name": "Alice",
            "container_type_id": "white",
            "quantity": 3,
            "content_type_ids": [],
            "note": None,
        },
    )

    r = client.post(
        "/api/movements/receive",
        json={
            "name": "Alice",
            "container_type_id": "white",
            "quantity": 2,
            "content_type_ids": ["veg"],
            "note": "Returned boxes",
        },
    )
    assert r.status_code == 201
    data = r.json()
    assert "transaction_id" in data
    assert data["direction"] == "IN"
    assert data["notes"] == "Returned boxes"
    assert data["primary_items"][0]["quantity"] == 2
    assert data["secondary_items"] == ["veg"]


def test_rich_receive_blocked_when_no_prior_issue(client):
    """
    POST /api/movements/receive should be blocked (422 or 400)
    when the client has no outstanding balance for that item.

    This validates the enforce_returns domain rule is active.
    """
    bootstrap_containers(client)

    r = client.post(
        "/api/movements/receive",
        json={
            "name": "Alice",
            "container_type_id": "white",
            "quantity": 1,
            "content_type_ids": [],
            "note": None,
        },
    )
    assert r.status_code in (400, 422)


# ---------------------------------------------------------------------------
# Summary / balance test
# ---------------------------------------------------------------------------


def test_summary_reflects_outstanding_after_rich_movements(client):
    """
    After issuing 3 and receiving 2, summary should show:
    - client_name = alice
    - total_outstanding = 1
    - grand_total = 1
    """
    bootstrap_containers(client)
    client.post(
        "/api/movements/issue",
        json={
            "name": "Alice",
            "container_type_id": "white",
            "quantity": 3,
            "content_type_ids": [],
            "note": None,
        },
    )
    client.post(
        "/api/movements/receive",
        json={
            "name": "Alice",
            "container_type_id": "white",
            "quantity": 2,
            "content_type_ids": [],
            "note": None,
        },
    )

    r = client.get("/api/summary")
    assert r.status_code == 200
    data = r.json()
    assert data["grand_total"] == 1
    assert data["clients"][0]["client_name"] == "alice"
    assert data["clients"][0]["total_outstanding"] == 1


# ---------------------------------------------------------------------------
# Guard test: old simple flow must remain unchanged
# ---------------------------------------------------------------------------


def test_old_simple_issue_still_works(client):
    """
    Guard test: POST /api/issue (simple container flow) must continue
    to work exactly as before the rich movements were introduced.

    This protects against accidental regressions when refactoring routes.
    """
    client.post("/api/container-types", json={"id": "white", "label": "White Box"})

    r = client.post(
        "/api/issue",
        json={"name": "Alice", "container_type_id": "white", "quantity": 2},
    )
    assert r.status_code == 200
    data = r.json()
    assert data["direction"] == "OUT"
    assert data["quantity"] == 2
    assert data["container_type_id"] == "white"
    assert "transaction_id" in data
