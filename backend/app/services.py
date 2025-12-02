import os
import requests
from typing import List, Dict, Optional

def fetch_fmp_articles(api_key: str, page: int = 0, limit: int = 50) -> List[Dict]:
    """
    Calls the FMP Stable endpoint.
    """
    url = "https://financialmodelingprep.com/stable/fmp-articles"
    
    params = {
        "page": page,
        "limit": limit,
        "apikey": api_key
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

        # Normalize response structure
        articles = data.get("content", data) if isinstance(data, dict) else data
        if not isinstance(articles, list):
            articles = []

        for item in articles:
            item["source_label"] = "FMP Articles"
            if "title" in item and "headline" not in item:
                item["headline"] = item["title"]

        return articles

    except Exception as e:
        print(f"[FMP] Request failed: {e}")
        return []

def get_all_news(ticker: Optional[str] = None, limit: int = 20, page: int = 0) -> List[Dict]:
    """
    Main function used by main.py.
    Reads API_KEY from environment variable.
    """
    # Retrieve API_KEY from environment (injected by K8s Secret)
    api_key = os.getenv("API_KEY")
    if not api_key:
        print("Error: API_KEY not found in environment variables.")
        return []

    articles = fetch_fmp_articles(api_key=api_key, page=page, limit=limit)

    # Client-side filtering for the specific ticker
    if ticker:
        ticker_upper = ticker.upper()
        filtered = [
            a for a in articles
            if ticker_upper in (a.get("headline", "") + a.get("title", "") + a.get("content", "")).upper()
        ]
        return filtered

    return articles