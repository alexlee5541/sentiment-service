# main.py
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
    init_db()
    print("Database Connected!")

    global sentiment_pipeline
    print("Loading FinBERT Model...")
    sentiment_pipeline = pipeline(
        "sentiment-analysis",
        model="yiyanghkust/finbert-tone",
        device=-1  # CPU
    )
    print("FinBERT Model Loaded!")
    yield
    sentiment_pipeline = None

app = FastAPI(lifespan=lifespan)

@app.get("/sentiment")
async def get_stock_sentiment(ticker: str, db: Session = Depends(get_db)):
    API_KEY = os.getenv("API_KEY")

    if not sentiment_pipeline:
        raise HTTPException(status_code=503, detail="AI Model is loading...")

    if not API_KEY:
        raise HTTPException(status_code=500, detail="FMP API Key missing")

    if not ticker or not ticker.strip():
        raise HTTPException(status_code=400, detail="Ticker symbol is required")

    ticker = ticker.strip().upper()

    # Fetch news for the specific ticker
    all_news = get_all_news(ticker=ticker, api_key=API_KEY, limit=20)

    if not all_news:
        raise HTTPException(status_code=404, detail=f"No news found for {ticker}")

    analyzed_news = []
    bullish_count = bearish_count = neutral_count = 0

    for item in all_news:
        headline = item.get("title", "").strip()
        if not headline:
            continue

        # FinBERT analysis
        result = sentiment_pipeline(headline[:512])[0]
        label = result['label']  # Positive, Negative, Neutral
        score = result['score']

        if label == "Positive":
            bullish_count += 1
        elif label == "Negative":
            bearish_count += 1
        else:
            neutral_count += 1

        # Save to database
        db_record = SentimentRecord(
            ticker=ticker,  # ← Make sure your DB model has this column!
            source=item.get('source_label', 'Unknown'),
            headline=headline[:200],
            sentiment=label,
            confidence=score
        )
        db.add(db_record)

        analyzed_news.append({
            "headline": headline,
            "sentiment": label,
            "confidence": round(score, 4),
            "source": item.get('source_label'),
            "published": item.get('publishedDate')
        })

    db.commit()

    # Determine overall sentiment
    total = bullish_count + bearish_count
    if total == 0:
        verdict = "Neutral"
    elif bullish_count > bearish_count:
        verdict = f"Bullish 🚀 ({bullish_count}/{total})"
    else:
        verdict = f"Bearish 📉 ({bearish_count}/{total})"

    return {
        "ticker": ticker,
        "verdict": verdict,
        "summary": {
            "bullish": bullish_count,
            "bearish": bearish_count,
            "neutral": neutral_count,
            "total_analyzed": len(analyzed_news)
        },
        "news": analyzed_news[:20]  # Limit output size
    }


@app.get("/history")
async def get_sentiment_history(ticker: str = None, db: Session = Depends(get_db)):
    query = db.query(SentimentRecord)
    if ticker:
        query = query.filter(SentimentRecord.ticker == ticker.upper())
    
    history = query.order_by(desc(SentimentRecord.created_at)).limit(100).all()
    
    return {
        "count": len(history),
        "records": [r.__dict__ for r in history]
    }