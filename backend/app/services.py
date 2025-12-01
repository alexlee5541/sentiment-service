# services.py
import os
import requests
from typing import List, Dict, Optional

def fetch_fmp_articles(
    api_key: str,
    page: int = 0,
    limit: int = 50
) -> List[Dict]:
    """
    Calls YOUR confirmed working endpoint:
    https://financialmodelingprep.com/stable/fmp-articles?page=0&limit=50&apikey=XXX
    """
    url = "https://financialmodelingprep.com/stable/fmp-articles"
    
    params = {
        "page": page,
        "limit": limit,
        "apikey": api_key   # ← directly from env var (injected by your backend.yaml)
    }

    try:
        response = requests.get(
            url,
            params=params,
            headers={"User-Agent": "FinancialSentimentApp/1.0"},
            timeout=15
        )
        response.raise_for_status()
        data = response.json()

        # FMP sometimes returns {"content": [...]} or direct list
        articles = data.get("content", data) if isinstance(data, dict) else data
        if not isinstance(articles, list):
            articles = []

        # Normalize fields + add source label
        for item in articles:
            item["source_label"] = "FMP Articles"
            # Some responses use 'title', some 'headline' — unify
            if "title" in item and "headline" not in item:
                item["headline"] = item["title"]

        return articles

    except Exception as e:
        print(f"[FMP] Request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"[FMP] Response: {e.response.text}")
        return []


def get_all_news(
    ticker: Optional[str] = None,
    limit: int = 20,
    page: int = 0
) -> List[Dict]:
    """
    Main function used by main.py
    Automatically reads API_KEY from environment (set by your backend.yaml)
    """
    api_key = os.getenv("API_KEY")
    if not api_key:
        raise ValueError("API_KEY environment variable is missing!")

    articles = fetch_fmp_articles(api_key=api_key, page=page, limit=limit)

    # Optional: filter by ticker (client-side)
    if ticker:
        ticker_upper = ticker.upper()
        filtered = [
            a for a in articles
            if ticker_upper in (a.get("headline", "") + a.get("title", "") + a.get("text", "")).upper()
        ]
        print(f"[FMP] {len(filtered)}/{len(articles)} articles mention {ticker}")
        return filtered

    return articles