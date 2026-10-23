
def test_health_endpoint_returns_success_and_database_status(client):
    response = client.get("/api/health")

    assert response.status_code == 200

    data = response.get_json()
    assert data["success"] is True
    assert data["data"]["status"] == "healthy"
    assert data["data"]["database"] == "connected"
