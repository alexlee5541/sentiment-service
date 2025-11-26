import requests

def fetch_fmp_data(url: str, api_key: str, limit: int = 20):
    """
    Generic helper to fetch data from FMP endpoints.
    """
    params = {"page": 0, "limit": limit, "apikey": api_key}
    try:
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Error fetching from {url}: {e}")
        return []

def get_all_news(api_key: str, limit: int = 20):
    """
    Aggregates news from multiple FMP endpoints.
    """
    sources = {
        "FMP Stable": "https://financialmodelingprep.com/stable/fmp-articles",
        "FMP General": "https://financialmodelingprep.com/stable/news/general-latest",
        "FMP Stock": "https://financialmodelingprep.com/stable/news/stock-latest",
    }

    aggregated_news = []
    for source_name, url in sources.items():
        items = fetch_fmp_data(url, api_key, limit)
        for item in items:
            item['source_label'] = source_name # Tag the source
        aggregated_news.extend(items)
    
    return aggregated_news