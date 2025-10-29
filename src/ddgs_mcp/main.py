"""
DDGS MCP Server - A metasearch MCP server using DDGS library.

This server provides comprehensive search capabilities through the Model Context Protocol,
integrating DDGS (Dux Distributed Global Search) with FastMCP framework.
"""

import json
import os
from typing import Annotated, Optional, Dict, Any
from pydantic import Field

from fastmcp import FastMCP
from ddgs import DDGS

# Initialize the FastMCP server
mcp = FastMCP(
    name="DDGS-MCP-Server",
    instructions="Metasearch server providing web, news search capabilities through DDGS library integration. Offers comprehensive search tools and resource templates.",
)

# Initialize DDGS client with proxy from environment variable if available
_proxy = os.getenv("DDGS_HTTP_PROXY")
_ddgs_client = DDGS(proxy=_proxy) if _proxy else DDGS()


@mcp.tool
def web_search(
    query: Annotated[str, Field(description="Search query string")],
    region: Annotated[
        str, Field(default="cn-zh", description="Region code (e.g., us-en, cn-zh)")
    ],
    max_results: Annotated[
        int, Field(default=10, ge=1, le=100, description="Maximum number of results")
    ],
    timelimit: Annotated[
        Optional[str], Field(default=None, description="Time limit: d, w, m, y")
    ] = None,
    backend: Annotated[
        str, Field(default="auto", description="Search backends (comma-separated)")
    ] = "auto",
) -> Dict[str, Any]:
    """
    Perform web search using DDGS metasearch engine.

    Searches across multiple search engines (Google, Bing, Brave, DuckDuckGo, etc.)
    with automatic fallback and deduplication.
    """
    try:
        results = _ddgs_client.text(
            query=query,
            region=region,
            max_results=max_results,
            safesearch="moderate",
            timelimit=timelimit,
            backend=backend,
        )

        return {
            "success": True,
            "query": query,
            "region": region,
            "results_count": len(results),
            "results": results,
            "backend": backend,
        }
    except Exception as e:
        return {"success": False, "error": str(e), "query": query}


@mcp.tool
def news_search(
    query: Annotated[str, Field(description="News search query")],
    region: Annotated[str, Field(default="us-en", description="Region code")],
    max_results: Annotated[
        int, Field(default=10, ge=1, le=100, description="Maximum number of results")
    ],
    timelimit: Annotated[
        Optional[str], Field(default=None, description="Time limit: d, w, m")
    ] = None,
) -> Dict[str, Any]:
    """
    Search for news articles using DDGS metasearch.

    Aggregates news from multiple sources with time-based filtering.
    """
    try:
        results = _ddgs_client.news(
            query=query, region=region, max_results=max_results, timelimit=timelimit
        )

        return {
            "success": True,
            "query": query,
            "timelimit": timelimit,
            "results_count": len(results),
            "results": results,
        }
    except Exception as e:
        return {"success": False, "error": str(e), "query": query}


# Resource Templates
@mcp.resource("search://web/{query}")
def web_search_resource(query: str) -> str:
    """Web search results as a JSON resource."""
    results = _ddgs_client.text(query, max_results=5)
    return json.dumps(
        {"query": query, "type": "web_search", "results": results}, indent=2
    )


@mcp.resource("search://news/{query}{?timelimit}")
def news_search_resource(query: str, timelimit: str = "w") -> str:
    """News search results as a JSON resource with optional time limit."""
    results = _ddgs_client.news(query, timelimit=timelimit, max_results=5)
    return json.dumps(
        {
            "query": query,
            "type": "news_search",
            "timelimit": timelimit,
            "results": results,
        },
        indent=2,
    )


def main() -> None:
    """
    Entry point for the DDGS MCP server.

    Run this server to provide search capabilities through MCP.

    Usage:
        ddgs-mcp

    The server will start with STDIO transport by default.
    """
    import sys

    if "--help" in sys.argv or "-h" in sys.argv:
        print("""
DDGS MCP Server - Metasearch capabilities through Model Context Protocol

Usage:
    ddgs-mcp                    # Start server with STDIO transport
    ddgs-mcp --http             # Start server with HTTP transport on port 8000
    ddgs-mcp --help             # Show this help message

Environment Variables:
    DDGS_HTTP_PROXY            # HTTP proxy for DDGS client (e.g., http://proxy:8080)

Available Tools:
    - web_search: Web search across multiple engines
    - news_search: News search with time filtering

Available Resources:
    - search://web/{query}
    - search://news/{query}{?timelimit}

""")
        return

    if "--http" in sys.argv:
        mcp.run(transport="http", host="127.0.0.1", port=10090, show_banner=False)
    else:
        mcp.run(show_banner=False)


if __name__ == "__main__":
    main()
