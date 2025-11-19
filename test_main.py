from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from main import app

# --- TECH LEAD LESSON: MOCKING ---
# We create a "Fake Model" so we don't download 500MB during tests.
mock_model_output = [{'label': 'Positive', 'score': 0.99}]
mock_pipeline = MagicMock()
mock_pipeline.return_value = mock_model_output

def test_health_check():
    """
    We patch 'main.pipeline'. This intercepts the call to HuggingFace.
    Instead of downloading, it instantly returns our 'mock_pipeline'.
    """
    with patch("main.pipeline", return_value=mock_pipeline):
        # We use 'with TestClient' to trigger the lifespan (startup) event
        with TestClient(app) as client:
            response = client.get("/health")
            assert response.status_code == 200
            # Now this should be True because we faked the download success
            assert response.json() == {"status": "active", "model_loaded": True}

def test_predict_endpoint_mock():
    with patch("main.pipeline", return_value=mock_pipeline):
        with TestClient(app) as client:
            response = client.post("/predict", json={"text": "This is a test."})
            
            assert response.status_code == 200
            data = response.json()
            assert data["sentiment"] == "Positive"
            assert data["confidence"] == 0.99