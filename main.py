import os
import requests
from fastapi import FastAPI, HTTPException, Depends
from contextlib import asynccontextmanager
from transformers import pipeline
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# Import our new database module
from database import SessionLocal, SentimentRecord, init_db

load_dotenv()
API_KEY = os.getenv("FIN_NEWS_API_KEY")

sentiment_pipeline = None

# --- DB DEPENDENCY ---
# This gives each request a fresh database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # 1. Initialize Database Tables
    print("Initializing Database...")
    try:
        init_db()
        print("Database Connected!")
    except Exception as e:
        print(f"Database Error: {e}")

    # 2. Load AI Model
    global sentiment_pipeline
    print("Loading FinBERT AI Model...")
    sentiment_pipeline = pipeline("sentiment-analysis", model="yiyanghkust/finbert-tone", device=-1)
    print("AI Ready!")
    yield
    sentiment_pipeline = None

app = FastAPI(lifespan=lifespan)

# --- SERVICE LAYER (Same as Phase 4) ---
def fetch_news_from_fmp_stable(limit: int = 50):
    url = "https://financialmodelingprep.com/stable/fmp-articles"
    params = {"page": 0, "limit": limit, "apikey": API_KEY}
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error: {e}")
        return []

# --- ENDPOINT ---
@app.get("/sentiment")
# Add 'db: Session' here to get access to the database
async def get_stock_sentiment(db: Session = Depends(get_db)):
    if not sentiment_pipeline:
        raise HTTPException(status_code=503, detail="AI Model is loading...")

    news_items = fetch_news_from_fmp_stable(limit=10)
    
    analyzed_news = []
    bullish_count = 0
    bearish_count = 0

    for item in news_items:
        headline = item.get("title", "")
        if not headline: continue

        # AI Analysis
        result = sentiment_pipeline(headline[:512])[0]
        label = result['label']
        score = result['score']

        if label == 'Positive': bullish_count += 1
        if label == 'Negative': bearish_count += 1

        # --- SAVE TO DATABASE (The New Part) ---
        # Create the record object
        db_record = SentimentRecord(
            source="FMP Stable",
            headline=headline[:200], # Truncate for DB safety
            sentiment=label,
            confidence=score
        )
        # Add to session
        db.add(db_record)
        
        analyzed_news.append({
            "headline": headline,
            "sentiment": label,
            "confidence": round(score, 2)
        })

    # Commit the transaction (Save all records at once)
    db.commit()

    verdict = "Neutral"
    if bullish_count > bearish_count: verdict = "Bullish 🚀"
    if bearish_count > bullish_count: verdict = "Bearish 📉"

    return {
        "database_status": "Records Saved ✅",
        "verdict": verdict,
        "news": analyzed_news
    }

    # Add 'desc' to imports to sort by newest first
from sqlalchemy import desc 

@app.get("/history")
async def get_sentiment_history(db: Session = Depends(get_db)):
    # SQL Equivalent: SELECT * FROM sentiment_records ORDER BY id DESC LIMIT 100;
    history = db.query(SentimentRecord)\
        .order_by(desc(SentimentRecord.id))\
        .limit(100)\
        .all()
    
    return {
        "count": len(history),
        "records": history
    }