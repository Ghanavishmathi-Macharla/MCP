import os
import requests

def normalize_name(value: str) -> str:
    """
    Normalize a company/ticker string for matching.

    Example:
        "Microsoft Corporation" -> "microsoft corporation"
        "Microsoft Corp."       -> "microsoft corp"
    """
    return (
        value.lower()
        .replace(",", "")
        .replace(".", "")
        .strip()
    )


def resolve_stock_symbol(query: str) -> dict:
    """
    Resolve a company name or ticker symbol to a stock.

    Resolution priority:
    1. Exact ticker
    2. Exact company name
    3. Normalized exact company name
    4. Strong name prefix match
    5. Ambiguous / not found
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

    response = requests.get(
        "https://finnhub.io/api/v1/search",
        params={
            "q": query,
            "token": api_key,
        },
        timeout=10,
    )

    response.raise_for_status()

    results = response.json().get("result", [])

    results = [
        r for r in results
        if r.get("symbol") and r.get("description")
    ]

    if not results:
        return {
            "status": "not_found",
            "message": f"No stock found for '{query}'."
        }

    query_upper = query.upper()
    query_normalized = normalize_name(query)

    # 1. Exact ticker
    exact_symbol = [
        r for r in results
        if r["symbol"].upper() == query_upper
    ]

    if len(exact_symbol) == 1:
        r = exact_symbol[0]

        return {
            "status": "resolved",
            "symbol": r["symbol"],
            "name": r["description"],
        }

    # 2. Exact company name
    exact_name = [
        r for r in results
        if normalize_name(r["description"]) == query_normalized
    ]

    if len(exact_name) == 1:
        r = exact_name[0]

        return {
            "status": "resolved",
            "symbol": r["symbol"],
            "name": r["description"],
        }

    # 3. Strong prefix match
    prefix_matches = [
        r for r in results
        if normalize_name(r["description"]).startswith(query_normalized)
    ]

    if len(prefix_matches) == 1:
        r = prefix_matches[0]

        return {
            "status": "resolved",
            "symbol": r["symbol"],
            "name": r["description"],
        }

    # 4. Multiple candidates
    matches = [
        {
            "symbol": r["symbol"],
            "name": r["description"],
            "type": r.get("type"),
            "display_symbol": r.get("displaySymbol"),
        }
        for r in results[:10]
    ]

    return {
        "status": "ambiguous",
        "message": f"Multiple stocks matched '{query}'.",
        "matches": matches,
    }