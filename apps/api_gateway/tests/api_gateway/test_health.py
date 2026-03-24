def test_health_check(test_client):
    response = test_client.get("/health")
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "api-gateway"
    assert data["environment"] == "development"