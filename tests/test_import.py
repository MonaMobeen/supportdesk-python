import io


def test_import_mixed_valid_invalid_rows(client):
    csv_content = (
        "title,description,requester,category,priority\n"
        "Valid ticket,Description here,Ali Khan,Bug,High\n"
        ",Missing title,Sara Khan,Bug,Medium\n"
        "Bad priority,Testing bad priority,Zain,Bug,Urgent\n"
    )

    file = io.BytesIO(csv_content.encode("utf-8"))
    response = client.post(
        "/tickets/import",
        files={"file": ("test.csv", file, "text/csv")}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["successful_count"] == 1
    assert data["failed_count"] == 2
    assert len(data["failed_rows"]) == 2