import os
import requests


def resolve_stock_symbol(query: str) -> str:
    """
    Resolve a company name or stock symbol to a stock ticker.

    Examples:
        NVIDIA -> NVDA
        Nvidia -> NVDA
        NVDA   -> NVDA
        Apple  -> AAPL
        AAPL   -> AAPL
    """

    query = query.strip()

    if not query:
        raise ValueError("Stock name or symbol cannot be empty")

    api_key = os.getenv("FINNHUB_API_KEY")

    if not api_key:
        raise RuntimeError("FINNHUB_API_KEY is not configured")

    # First try Finnhub's symbol search
    url = "https://finnhub.io/api/v1/search"

    params = {
        "q": query,
        "token": api_key,
    }

    response = requests.get(
        url,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    results = data.get("result", [])

    if not results:
        raise ValueError(
            f"Could not find a stock for '{query}'"
        )

    # Look for an exact ticker match first.
    query_upper = query.upper()

    for result in results:
        symbol = result.get("symbol", "")

        if symbol.upper() == query_upper:
            return symbol

    # Otherwise look for an exact company-name match.
    query_lower = query.lower()

    for result in results:
        description = result.get("description", "")

        if description.lower() == query_lower:
            return result["symbol"]

    # Otherwise use the first result.
    return results[0]["symbol"]
    