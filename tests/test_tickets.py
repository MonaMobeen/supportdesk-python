def test_create_valid_ticket(client):
    response = client.post("/tickets/", json={
        "title": "Test ticket",
        "description": "Test description",
        "requester": "Ali Khan",
        "category": "Bug",
        "priority": "High"
    })
    assert response.status_code == 200
    assert response.json()["status"] == "Open"


def test_create_ticket_missing_title(client):
    response = client.post("/tickets/", json={
        "description": "No title given",
        "requester": "Ali Khan",
        "category": "Bug"
    })
    assert response.status_code == 422  # Pydantic validation error


def test_create_ticket_invalid_priority(client):
    response = client.post("/tickets/", json={
        "title": "Test",
        "description": "Test",
        "requester": "Ali Khan",
        "category": "Bug",
        "priority": "Urgent"
    })
    assert response.status_code == 422


def test_valid_status_transition(client):
    create_res = client.post("/tickets/", json={
        "title": "Test", "description": "Test",
        "requester": "Ali", "category": "Bug"
    })
    ticket_id = create_res.json()["id"]

    response = client.put(f"/tickets/{ticket_id}", json={"status": "In Progress"})
    assert response.status_code == 200
    assert response.json()["status"] == "In Progress"


def test_forbidden_status_transition(client):
    create_res = client.post("/tickets/", json={
        "title": "Test", "description": "Test",
        "requester": "Ali", "category": "Bug"
    })
    ticket_id = create_res.json()["id"]

    # Open -> Resolved seedha allowed nahi
    response = client.put(f"/tickets/{ticket_id}", json={"status": "Resolved"})
    assert response.status_code == 400
    assert "Cannot change status" in response.json()["detail"]


def test_close_without_resolution_note(client):
    create_res = client.post("/tickets/", json={
        "title": "Test", "description": "Test",
        "requester": "Ali", "category": "Bug"
    })
    ticket_id = create_res.json()["id"]

    response = client.put(f"/tickets/{ticket_id}", json={"status": "Closed"})
    assert response.status_code == 400
    assert "Resolution note is required" in response.json()["detail"]


def test_assign_to_valid_agent(client):
    client.post("/agents/", json={"name": "Sara Ahmed", "email": "sara@test.com"})

    create_res = client.post("/tickets/", json={
        "title": "Test", "description": "Test",
        "requester": "Ali", "category": "Bug"
    })
    ticket_id = create_res.json()["id"]

    response = client.put(f"/tickets/{ticket_id}", json={"assigned_agent": "Sara Ahmed"})
    assert response.status_code == 200
    assert response.json()["assigned_agent"] == "Sara Ahmed"


def test_assign_to_invalid_agent(client):
    create_res = client.post("/tickets/", json={
        "title": "Test", "description": "Test",
        "requester": "Ali", "category": "Bug"
    })
    ticket_id = create_res.json()["id"]

    response = client.put(f"/tickets/{ticket_id}", json={"assigned_agent": "Fake Agent"})
    assert response.status_code == 400
    assert "does not exist" in response.json()["detail"]


def test_reassign_ticket_to_different_agent(client):
    client.post("/agents/", json={"name": "Agent A", "email": "a@test.com"})
    client.post("/agents/", json={"name": "Agent B", "email": "b@test.com"})

    create_res = client.post("/tickets/", json={
        "title": "Test", "description": "Test",
        "requester": "Ali", "category": "Bug"
    })
    ticket_id = create_res.json()["id"]

    client.put(f"/tickets/{ticket_id}", json={"assigned_agent": "Agent A"})
    response = client.put(f"/tickets/{ticket_id}", json={"assigned_agent": "Agent B"})

    assert response.status_code == 200
    assert response.json()["assigned_agent"] == "Agent B"


def test_search_filter(client):
    client.post("/tickets/", json={
        "title": "Login broken", "description": "Cannot login",
        "requester": "Ali", "category": "Bug", "priority": "High"
    })
    client.post("/tickets/", json={
        "title": "Printer issue", "description": "Not printing",
        "requester": "Sara", "category": "Hardware", "priority": "Low"
    })

    response = client.get("/tickets/?search=login")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert "Login" in data["results"][0]["title"]


def test_status_filter(client):
    create_res = client.post("/tickets/", json={
        "title": "Test", "description": "Test",
        "requester": "Ali", "category": "Bug"
    })
    ticket_id = create_res.json()["id"]
    client.put(f"/tickets/{ticket_id}", json={"status": "In Progress"})

    response = client.get("/tickets/?status=In Progress")
    assert response.status_code == 200
    assert response.json()["total"] == 1