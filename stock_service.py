import os
import requests

def resolve_stock_symbol(query: str) -> dict:
    """
    Resolve a company name or ticker symbol.

    Returns:
        {
            "status": "resolved",
            "symbol": "NVDA",
            "name": "NVIDIA Corporation"
        }

    or:

        {
            "status": "ambiguous",
            "matches": [...]
        }

    or:

        {
            "status": "not_found",
            "message": "..."
        }
    """

    query = query.strip()

    if not query:
        return {
            "status": "not_found",
            "message": "Stock name or symbol cannot be empty."
        }

    api_key = os.getenv("FINNHUB_API_KEY")

    if not api_key:
        raise RuntimeError("FINNHUB_API_KEY is not configured")

    url = "https://finnhub.io/api/v1/search"

    params = {
        "q": query,
        "token": api_key
    }

    response = requests.get(
        url,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    results = data.get("result", [])

    # Only keep actual common-stock results.
    results = [
        result
        for result in results
        if result.get("symbol")
        and result.get("description")
    ]

    if not results:
        return {
            "status": "not_found",
            "message": f"No stock found for '{query}'."
        }

    query_upper = query.upper()
    query_lower = query.lower()

    # --------------------------------------------------
    # 1. Exact ticker match
    # --------------------------------------------------

    exact_symbol_matches = [
        result
        for result in results
        if result["symbol"].upper() == query_upper
    ]

    if len(exact_symbol_matches) == 1:
        result = exact_symbol_matches[0]

        return {
            "status": "resolved",
            "symbol": result["symbol"],
            "name": result["description"]
        }

    # --------------------------------------------------
    # 2. Exact company-name match
    # --------------------------------------------------

    exact_name_matches = [
        result
        for result in results
        if result["description"].lower() == query_lower
    ]

    if len(exact_name_matches) == 1:
        result = exact_name_matches[0]

        return {
            "status": "resolved",
            "symbol": result["symbol"],
            "name": result["description"]
        }

    # --------------------------------------------------
    # 3. Multiple possible matches
    # --------------------------------------------------

    matches = [
        {
            "symbol": result["symbol"],
            "name": result["description"],
            "type": result.get("type"),
            "display_symbol": result.get("displaySymbol")
        }
        for result in results[:10]
    ]

    return {
        "status": "ambiguous",
        "message": f"Multiple stocks matched '{query}'.",
        "matches": matches
    }