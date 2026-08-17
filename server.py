from mcp.server import MCPServer
import os
import requests
from dotenv import load_dotenv

load_dotenv()

mcp = MCPServer("Financial Assistant")

# @mcp.tool()
# def add(a: int, b: int) -> int:
#     """Add two numbers."""
#     return a + b

@mcp.tool()
def get_stock_price(symbol: str) -> dict:
    """
    Get the current stock price for a given symbol.
    Use this tool whenever the user asks for a current,
    live, or latest stock price.
    """

    api_key = os.getenv("FINNHUB_API_KEY")

    if not api_key :
        return {
            "error": "API key not found. Please set the FINNHUB_API_KEY environment variable."
        }

    symbol = symbol.strip().upper()

    if not symbol:
        return {
            "error": "Stock symbol cannot be empty."
        }

    url = "https://finnhub.io/api/v1/quote"
    params = {
        "symbol": symbol,
        "token": api_key
    }

    try:
      response = requests.get(url, params=params,timeout=10)
      response.raise_for_status()  # If the HTTP request failed, raise an exception instead of pretending everything worked.
      data = response.json()

      if not data or data.get("c") is None:
          return {
              "error": f"No data found for symbol: {symbol}"
          }

      return {
          "symbol": symbol.upper(),
          "current_price": data["c"],
          "change": data["d"],
          "change_percent": data["dp"],
          "high": data["h"],
          "low": data["l"],
          "open": data["o"],
          "previous_close": data["pc"],
          "timestamp": data["t"],
      }
    
    except requests.RequestException as e:
      return {
          "error":  f"Failed to fetch stock data: {str(e)}"
      }

if __name__ == "__main__":
    mcp.run("stdio")
