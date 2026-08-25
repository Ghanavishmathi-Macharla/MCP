from mcp.server import MCPServer
import os
import requests
from dotenv import load_dotenv
from gmail import send_email as gmail_send_email
from stock_service import resolve_stock_symbol

load_dotenv()

mcp = MCPServer("Financial Assistant")

# @mcp.tool()
# def add(a: int, b: int) -> int:
#     """Add two numbers."""
#     return a + b

def fetch_stock_quote(symbol: str) -> dict:
    api_key = os.getenv("FINNHUB_API_KEY")

    if not api_key:
        raise RuntimeError("FINNHUB_API_KEY is not configured")

    symbol = symbol.strip().upper()

    if not symbol:
        raise ValueError("Stock symbol cannot be empty")

    url = "https://finnhub.io/api/v1/quote"

    params = {
        "symbol": symbol,
        "token": api_key,
    }

    response = requests.get(
        url,
        params=params,
        timeout=10
    )

    response.raise_for_status()

    data = response.json()

    if not data or data.get("c") is None:
        raise ValueError(
            f"No quote data found for symbol '{symbol}'"
        )

    return {
        "symbol": symbol,
        "current_price": data["c"],
        "change": data["d"],
        "change_percent": data["dp"],
        "high": data["h"],
        "low": data["l"],
        "open": data["o"],
        "previous_close": data["pc"],
        "timestamp": data["t"],
    }

@mcp.tool()
def get_stock_price(symbol: str) -> dict:
    """
    Get the latest available stock quote.

    The input can be either:
    - a ticker symbol, such as AAPL or NVDA
    - a company name, such as Apple or NVIDIA

    Company names are automatically resolved to ticker symbols.
    """

    try:
        resolution = resolve_stock_symbol(symbol)

        if resolution["status"] == "not_found":
            return resolution

        if resolution["status"] == "ambiguous":
            return resolution

        resolved_symbol = resolution["symbol"]

        quote = fetch_stock_quote(resolved_symbol)

        return {
            "requested": symbol,
            "company": resolution["name"],
            **quote
        }

    except requests.RequestException as e:
        return {
            "status": "error",
            "message": f"Failed to fetch stock data: {str(e)}"
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }
    
@mcp.tool()
def send_email(
    to: str,
    subject: str,
    body: str
) -> dict:
    """
    Send an email using the authenticated Gmail account.
    """

    try:
        return gmail_send_email(
            to=to,
            subject=subject,
            body=body
        )

    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }

@mcp.tool()
def compare_stocks(stock1: str, stock2: str) -> dict:
    """
    Compare two stocks using their latest available quotes.
    """

    try:
        resolution1 = resolve_stock_symbol(stock1)
        resolution2 = resolve_stock_symbol(stock2)

        if resolution1["status"] != "resolved":
            return {
                "status": "error",
                "stock": stock1,
                "resolution": resolution1,
            }

        if resolution2["status"] != "resolved":
            return {
                "status": "error",
                "stock": stock2,
                "resolution": resolution2,
            }

        quote1 = fetch_stock_quote(resolution1["symbol"])
        quote2 = fetch_stock_quote(resolution2["symbol"])

        performance_difference = (
            quote1["change_percent"] -
            quote2["change_percent"]
        )

        return {
            "status": "success",
            "comparison": {
                "stock_1": {
                    "requested": stock1,
                    "company": resolution1["name"],
                    **quote1,
                },
                "stock_2": {
                    "requested": stock2,
                    "company": resolution2["name"],
                    **quote2,
                },
                "performance_difference_percent": performance_difference,
            },
        }

    except requests.RequestException as e:
        return {
            "status": "error",
            "message": f"Failed to fetch stock data: {str(e)}",
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }
    
@mcp.resource("watchlist://stocks")
def get_watchlist() -> str:
   return """
        AAPL
        MSFT
        GOOGL
        AMZN
        NVDA
    """

@mcp.resource("stock://{symbol}")
def get_stock_resource(symbol: str) -> dict:
    """Provide stock information as an MCP resource."""

    try:
        return fetch_stock_quote(symbol)

    except (RuntimeError, ValueError) as e:
        return {
            "error": str(e)
        }

    except requests.RequestException as e:
        return {
            "error": f"Failed to fetch stock data: {str(e)}"
        }
    
@mcp.prompt()
def analyze_stock(symbol: str) -> str:
    """Generate a structured prompt for analyzing a stock."""

    return f"""
    Analyze the stock {symbol.upper()}.

    Use the available stock information and provide:

    1. Current price
    2. Daily price change
    3. Daily percentage change
    4. Day high
    5. Day low
    6. Previous closing price
    7. A short interpretation of the current movement

    Clearly mention that this is market data and not financial advice.
    """

if __name__ == "__main__":
    mcp.run("stdio")
