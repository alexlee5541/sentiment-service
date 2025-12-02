import os
from fastapi import FastAPI, HTTPException, Depends
from contextlib import asynccontextmanager
from transformers import pipeline
from dotenv import load_dotenv
from sqlalchemy.orm import Session
from sqlalchemy import desc

from .database import SessionLocal, SentimentRecord, init_db
from .services import get_all_news

load_dotenv()

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
        print(f"Database Init Error: {e}")

    global sentiment_pipeline
    print("Loading FinBERT Model...")
    sentiment_pipeline = pipeline("sentiment-analysis", model="yiyanghkust/finbert-tone", device=-1)
    print("FinBERT Model Loaded!")
    yield
    sentiment_pipeline = None

app = FastAPI(lifespan=lifespan)

@app.get("/sentiment")
async def get_stock_sentiment(ticker: str, db: Session = Depends(get_db)):
    if not sentiment_pipeline:
        raise HTTPException(status_code=503, detail="AI Model is loading...")

    # Use logic to fetch news (API key is handled inside services.py now)
    all_news = get_all_news(ticker=ticker, limit=50)

    if not all_news:
        # Return a 200 OK with empty data instead of 404 to avoid frontend crashes
        return {
            "ticker": ticker,
            "verdict": "Neutral (No News Found)",
            "news": []
        }

    analyzed_news = []
    bullish_count = 0
    bearish_count = 0

    for item in all_news:
        headline = item.get("headline", "") or item.get("title", "")
        if not headline: continue

        # AI Inference
        result = sentiment_pipeline(headline[:512])[0]
        label = result['label']
        score = result['score']

        if label == 'Positive': bullish_count += 1
        if label == 'Negative': bearish_count += 1

        # Save to DB
        try:
            db_record = SentimentRecord(
                ticker=ticker,
                source=item.get('source_label', 'FMP'),
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
        except Exception as e:
            print(f"DB Save Error: {e}")

    db.commit()

    verdict = "Neutral"
    if bullish_count > bearish_count: verdict = "Bullish 🚀"
    if bearish_count > bullish_count: verdict = "Bearish 📉"

    return {
        "ticker": ticker,
        "verdict": verdict,
        "news": analyzed_news
    }

@app.get("/history")
async def get_sentiment_history(db: Session = Depends(get_db)):
    history = db.query(SentimentRecord).order_by(desc(SentimentRecord.created_at)).limit(100).all()
    return {"count": len(history), "records": history}