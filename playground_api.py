import json
import os

from starlette.applications import Starlette
from starlette.responses import JSONResponse, FileResponse
from starlette.routing import Route
from starlette.middleware import Middleware
from starlette.middleware.cors import CORSMiddleware

from server import get_stock_price, get_watchlist, fetch_stock_quote
from stock_service import resolve_stock_symbol


async def index(request):
    return FileResponse("mcp_playground.html")


async def tools_list(request):
    tools = [
        {
            "name": "get_stock_price",
            "description": "Get the latest available stock quote.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "symbol": {
                        "type": "string",
                        "description": "Ticker symbol or company name",
                    }
                },
                "required": ["symbol"],
            },
        },
        {
            "name": "send_email",
            "description": "Send an email using the authenticated Gmail account.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "to": {"type": "string"},
                    "subject": {"type": "string"},
                    "body": {"type": "string"},
                },
                "required": ["to", "subject", "body"],
            },
        },
        {
            "name": "compare_stocks",
            "description": "Compare two stocks using their latest available quotes.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "stock1": {"type": "string"},
                    "stock2": {"type": "string"},
                },
                "required": ["stock1", "stock2"],
            },
        },
    ]
    return JSONResponse({"tools": tools})


async def tools_call(request):
    body = await request.json()
    name = body.get("name", "")
    arguments = body.get("arguments", {})

    if name == "get_stock_price":
        result = get_stock_price(arguments.get("symbol", ""))
    else:
        return JSONResponse(
            {"error": f"Tool '{name}' is not available in live demo"},
            status_code=400,
        )

    return JSONResponse({"result": result})


async def resources_list(request):
    resources = [
        {
            "uri": "watchlist://stocks",
            "name": "Stock Watchlist",
            "description": "Current stock watchlist",
        }
    ]
    return JSONResponse({"resources": resources})


async def resources_read(request):
    uri = request.query_params.get("uri", "")
    if uri == "watchlist://stocks":
        text = get_watchlist().strip()
        return JSONResponse(
            {"contents": [{"uri": uri, "text": text}]}
        )
    return JSONResponse({"error": "Resource not found"}, status_code=404)


async def resolve(request):
    """Resolve a company name to a ticker symbol (used by the flow animation)."""
    symbol = request.query_params.get("symbol", "")
    result = resolve_stock_symbol(symbol)
    return JSONResponse(result)


app = Starlette(
    routes=[
        Route("/", index),
        Route("/api/tools/list", tools_list),
        Route("/api/tools/call", tools_call, methods=["POST"]),
        Route("/api/resources/list", resources_list),
        Route("/api/resources/read", resources_read),
        Route("/api/resolve", resolve),
    ],
    middleware=[
        Middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        ),
    ],
)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8088)
