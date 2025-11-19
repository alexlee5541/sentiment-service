from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from contextlib import asynccontextmanager
from transformers import pipeline

# Global variable to hold the model
sentiment_pipeline = None

# --- LIFESPAN EVENT (The "Tech Lead" Way) ---
# This runs ONCE when the server starts, not per request.
@asynccontextmanager
async def lifespan(app: FastAPI):
    global sentiment_pipeline
    print("Loading AI Model... (This might take a few seconds)")
    try:
        # We load the model specifically for CPU to save RAM
        sentiment_pipeline = pipeline(
            "sentiment-analysis", 
            model="yiyanghkust/finbert-tone",
            device=-1  # device=-1 forces CPU usage
        )
        print("AI Model Loaded Successfully!")
    except Exception as e:
        print(f"Failed to load model: {e}")
    yield
    # Clean up resources if needed (runs on shutdown)
    sentiment_pipeline = None
    print("Model unloaded.")

app = FastAPI(lifespan=lifespan)

# --- CONTRACT ---
class NewsRequest(BaseModel):
    text: str

# --- ENDPOINTS ---
@app.post("/predict")
async def predict(request: NewsRequest):
    if not sentiment_pipeline:
        raise HTTPException(status_code=503, detail="Model is not ready.")
    
    # The actual inference
    try:
        # Result comes back as a list of dicts: [{'label': 'Neutral', 'score': 0.99}]
        result = sentiment_pipeline(request.text)[0]
        return {
            "sentiment": result['label'], 
            "confidence": round(result['score'], 4),
            "input_preview": request.text[:50] + "..."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "active", "model_loaded": sentiment_pipeline is not None}