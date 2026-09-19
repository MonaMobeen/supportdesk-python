from unittest.mock import patch


def test_database_failure_on_create(client):
    with patch("app.services.ticket_service.Ticket") as MockTicket:
        MockTicket.side_effect = Exception("Database connection lost")

        response = client.post("/tickets/", json={
            "title": "Test", "description": "Test",
            "requester": "Ali", "category": "Bug"
        })

        # Global exception handler ki wajah se 500 aana chahiye, raw crash nahi
        assert response.status_code == 500
        assert response.json()["detail"] == "An unexpected error occurred. Please try again later."