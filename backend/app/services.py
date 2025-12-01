import requests

def fetch_fmp_data(url: str, api_key: str, params: dict, limit: int = 20):
    """
    Generic helper to fetch data from FMP endpoints.
    Combines static and dynamic parameters.
    """
    # Combine user-defined params with global settings
    final_params = {"limit": limit, "apikey": api_key}
    final_params.update(params)

    try:
        # Increase timeout to 10 seconds for external API calls
        response = requests.get(url, params=final_params, timeout=10)
        # Will raise HTTPError for 4xx or 5xx status codes
        response.raise_for_status() 
        return response.json()
    except Exception as e:
        # We print the error but return an empty list so the FastAPI loop doesn't crash
        print(f"Error fetching from {url} with params {final_params}: {e}")
        return []

# FIX: Ticker argument is still needed for the main.py function signature,
# but we will ignore it here and only fetch general news.
def get_all_news(api_key: str, ticker: str, limit: int = 20):
    """
    Fetches news using only the general FMP Stable endpoint, as requested.
    The 'ticker' argument is ignored in this implementation.
    """
    aggregated_news = []
    
    # 1. Fetch General Market News (Only use this endpoint)
    general_url = "https://financialmodelingprep.com/api/v3/fmp-articles"
    
    # We fetch the full limit of news since this is the only source
    general_items = fetch_fmp_data(
        url=general_url,
        api_key=api_key,
        params={},
        limit=limit 
    )
    
    for item in general_items:
        item['source_label'] = "FMP Stable Market News"
        if item.get('title'):
            aggregated_news.append(item)
            
    # CRITICAL CHANGE: The FastAPI logic is still designed for a ticker,
    # but since we are only getting general news, every analysis performed
    # will be based on the general market conditions, not specific to the ticker.
    
    return aggregated_news