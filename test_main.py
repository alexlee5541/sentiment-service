from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_check():
    """
    Tech Lead Note: This is a 'Smoke Test'. 
    It verifies the API starts and returns 200 OK.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "active", "model_loaded": True}

def test_predict_endpoint_mock():
    """
    Ideally, we mock the AI model here so we don't load 500MB of data during tests.
    For now, we will just test that the endpoint exists and handles bad input.
    """
    response = client.post("/predict", json={"text": "This is a test."})
    # Since the model loads at startup, this might actually run inference.
    # In a strictly 'unit' test, we would mock 'sentiment_pipeline'.
    assert response.status_code == 200
    assert "sentiment" in response.json()