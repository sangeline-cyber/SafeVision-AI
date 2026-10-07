def test_backend_health_endpoint(client):
    """
    Test GET /api/health returns exact expected response:
    {
      "status": "ok",
      "service": "SafeVision AI"
    }
    """
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "SafeVision AI"


def test_database_health_endpoint(client):
    """
    Test GET /api/health/database returns structured health schema.
    """
    response = client.get("/api/health/database")
    # Response can be 200 (if connected) or 503 (if PostgreSQL is not currently running locally)
    assert response.status_code in [200, 503]
    data = response.json()
    assert "status" in data
    assert "connected" in data
    assert "database" in data
    assert isinstance(data["connected"], bool)
