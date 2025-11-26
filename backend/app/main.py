import os
from fastapi import FastAPI, HTTPException, Depends
from contextlib import asynccontextmanager
from transformers import pipeline
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import desc

# Relative imports
from .database import SessionLocal, SentimentRecord, init_db
from .services import get_all_news

load_dotenv()
API_KEY = os.getenv("FIN_NEWS_API_KEY")

sentiment_pipeline = None

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Initializing Database...")
    try:
        init_db()
        print("Database Connected!")
    except Exception as e:
        print(f"Database Error: {e}")

    global sentiment_pipeline
    print("Loading FinBERT AI Model...")
    # Use device=-1 for CPU
    sentiment_pipeline = pipeline("sentiment-analysis", model="yiyanghkust/finbert-tone", device=-1)
    print("AI Ready!")
    yield
    sentiment_pipeline = None

app = FastAPI(lifespan=lifespan)

@app.get("/sentiment")
async def get_stock_sentiment(db: Session = Depends(get_db)):
    if not sentiment_pipeline:
        raise HTTPException(status_code=503, detail="AI Model is loading...")
    
    if not API_KEY:
        raise HTTPException(status_code=500, detail="API Key missing")

    # 1. Fetch Data (Using the new service layer)
    all_news = get_all_news(API_KEY, limit=20)
    
    analyzed_news = []
    bullish_count = 0
    bearish_count = 0

    # 2. Process
    for item in all_news:
        headline = item.get("title", "")
        if not headline: continue

        # Truncate for BERT safety
        result = sentiment_pipeline(headline[:512])[0]
        label = result['label']
        score = result['score']

        if label == 'Positive': bullish_count += 1
        if label == 'Negative': bearish_count += 1

        # 3. Save
        db_record = SentimentRecord(
            source=item.get('source_label', 'Unknown'),
            headline=headline[:200],
            sentiment=label,
            confidence=score
        )
        db.add(db_record)
        
        analyzed_news.append({
            "headline": headline,
            "sentiment": label,
            "confidence": round(score, 2)
        })

    db.commit()

    verdict = "Neutral"
    if bullish_count > bearish_count: verdict = "Bullish 🚀"
    if bearish_count > bullish_count: verdict = "Bearish 📉"

    return {
        "database_status": "Records Saved ✅",
        "verdict": verdict,
        "news": analyzed_news
    }

@app.get("/history")
async def get_sentiment_history(db: Session = Depends(get_db)):
    history = db.query(SentimentRecord)\
        .order_by(desc(SentimentRecord.id))\
        .limit(100)\
        .all()
    return {"count": len(history), "records": history}