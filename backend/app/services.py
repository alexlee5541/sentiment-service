# services.py
import requests
from typing import List, Dict, Optional

def fetch_fmp_data(url: str, api_key: str, params: dict) -> List[Dict]:
    """
    Generic helper to fetch data from FMP endpoints.
    """
    # Merge custom params with API key
    full_params = {**params, "apikey": api_key}
    try:
        headers = {"User-Agent": "FinancialSentimentApp/1.0"}
        response = requests.get(url, params=full_params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        # Assume it's a list; handle if it's a dict with 'results'
        return data if isinstance(data, list) else data.get('results', [])
    except requests.exceptions.RequestException as e:
        print(f"Error fetching from {url}: {e}")
        return []


def get_all_news(api_key: str, ticker: Optional[str] = None, limit: int = 20, page: int = 0) -> List[Dict]:
    """
    Fetch general FMP articles. If ticker is provided, filter articles mentioning the ticker in headline/snippet.
    """
    base_url = "https://financialmodelingprep.com/api/v3/fmp/articles"  # Standard base; your /stable/ works too if preferred
    
    params = {
        "page": page,
        "limit": limit,  # Or use "size" if preferred—both often work
    }
    
    all_articles = fetch_fmp_data(base_url, api_key, params)
    
    # Add source label
    for item in all_articles:
        item['source_label'] = 'FMP Articles'
    
    # Optional: Filter by ticker (case-insensitive search in title/snippet)
    if ticker:
        ticker_upper = ticker.upper()
        filtered_articles = [
            item for item in all_articles
            if ticker_upper in (item.get('headline', '') + item.get('snippet', '')).upper()
        ]
        print(f"Filtered {len(all_articles) - len(filtered_articles)} articles; kept {len(filtered_articles)} mentioning {ticker}")
        return filtered_articles
    
    return all_articles