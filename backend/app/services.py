import requests

def fetch_fmp_data(url: str, api_key: str, page: int = 0, limit: int = 20, extra_params: dict | None = None):
    """
    Generic helper to fetch data from the new FMP /fmp-articles endpoint.
    The new endpoint expects ?page=...&limit=...&apikey=... directly in the query string.
    """
    params = {
        "page": page,
        "limit": limit,
        "apikey": api_key,
    }
    
    if extra_params:
        params.update(extra_params)

    try:
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching from {url} (page={page}, limit={limit}): {e}")
        return []


def get_all_news(api_key: str, ticker: str = "", limit: int = 20, page: int = 0):
    """
    Fetches general market news from the new FMP Stable endpoint:
    https://financialmodelingprep.com/stable/fmp-articles?page=X&limit=Y&apikey=KEY
    
    The `ticker` parameter is kept for backward compatibility with your FastAPI routes
    but is ignored (as the endpoint returns only general news).
    """
    aggregated_news = []

    # New official endpoint
    general_url = "https://financialmodelingprep.com/stable/fmp-articles"

    news_items = fetch_fmp_data(
        url=general_url,
        api_key=api_key,
        page=page,
        limit=limit
    )

    # FMP still returns a list of articles even on error sometimes → safeguard
    if isinstance(news_items, list):
        for item in news_items:
            item = item.copy()  # avoid mutating original if cached somewhere
            item['source_label'] = "FMP Stable Market News"
            if item.get('title'):  # only add valid articles
                aggregated_news.append(item)

    return aggregated_news