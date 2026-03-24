from unittest.mock import patch


def test_get_tasks_with_authors_success(test_client, mock_httpx_client):
    with patch("httpx.AsyncClient", return_value=mock_httpx_client):
        response = test_client.get("/tasks/with_authors/1")
        
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "test@example.com"
        
        assert len(mock_httpx_client.get_calls) == 1
        assert "receive_user_by_id/1" in mock_httpx_client.get_calls[0]["url"]


def test_get_tasks_with_authors_user_service_error(test_client, mock_httpx_client_error):
    with patch("httpx.AsyncClient", return_value=mock_httpx_client_error):
        response = test_client.get("/tasks/with_authors/1")
        
        assert response.status_code == 500
        data = response.json()
        assert "User service error" in data["detail"]
