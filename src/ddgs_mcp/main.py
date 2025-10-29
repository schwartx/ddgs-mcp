"""
DDGS MCP Server - A metasearch MCP server using DDGS library.

This server provides comprehensive search capabilities through the Model Context Protocol,
integrating DDGS (Dux Distributed Global Search) with FastMCP framework.
"""

import json
from typing import Annotated
from pydantic import Field
import typer

from fastmcp import FastMCP
from ddgs import DDGS

# Initialize the FastMCP server
mcp = FastMCP(
    name="DDGS-MCP-Server",
    instructions="Web and news search using DDGS metasearch engine.",
)

# Initialize DDGS client
_ddgs_client = DDGS()


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
        str | None, Field(default=None, description="Time limit: d, w, m, y")
    ] = None,
    backend: Annotated[
        str,
        Field(
            default="auto",
            description="Search backends: 'auto' or comma-separated list (text: bing,brave,duckduckgo,google,mojeek,mullvad_brave,mullvad_google,yahoo,wikipedia; news: bing,duckduckgo,yahoo)",
        ),
    ] = "auto",
) -> dict[str, object]:
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
            "query": query,
            "region": region,
            "backend": backend,
            "results_count": len(results),
            "results": results,
        }
    except Exception as e:
        raise RuntimeError(
            f"DDGS web search failed: {str(e)}. Check query parameters and backend availability."
        )


@mcp.tool
def news_search(
    query: Annotated[str, Field(description="News search query")],
    region: Annotated[
        str, Field(default="cn-zh", description="Region code (e.g., us-en, cn-zh)")
    ],
    max_results: Annotated[
        int, Field(default=10, ge=1, le=100, description="Maximum number of results")
    ],
    timelimit: Annotated[
        str | None, Field(default=None, description="Time limit: d, w, m")
    ] = None,
    backend: Annotated[
        str,
        Field(
            default="auto",
            description="News backends: 'auto' or comma-separated list from: bing,duckduckgo,yahoo",
        ),
    ] = "auto",
) -> dict[str, object]:
    """
    Search for news articles using DDGS metasearch.

    Aggregates news from multiple sources with time-based filtering.
    """
    try:
        results = _ddgs_client.news(
            query=query,
            region=region,
            max_results=max_results,
            timelimit=timelimit,
            backend=backend,
        )

        return {
            "query": query,
            "timelimit": timelimit,
            "backend": backend,
            "results_count": len(results),
            "results": results,
        }
    except Exception as e:
        raise RuntimeError(
            f"DDGS news search failed: {str(e)}. Check query parameters and backend availability."
        )


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


# Create typer app instance
app = typer.Typer(
    name="ddgs-mcp",
    help="DDGS MCP Server - Metasearch capabilities through Model Context Protocol",
    invoke_without_command=True,
    no_args_is_help=False,
    add_completion=False,
)


@app.callback(invoke_without_command=True)
def main(
    http: bool = typer.Option(
        False, "--http", help="Start server with HTTP transport instead of STDIO"
    ),
    host: str = typer.Option(
        "0.0.0.0", "--host", help="Host address for HTTP transport (default: 0.0.0.0)"
    ),
    port: int = typer.Option(
        10090, "--port", help="Port number for HTTP transport (default: 10090)"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Enable verbose logging output"
    ),
) -> None:
    """
    DDGS MCP Server - Provides search capabilities through Model Context Protocol.

    This server integrates DDGS (Dux Distributed Global Search) with FastMCP framework
    to provide comprehensive web and news search capabilities.

    Examples:
        ddgs-mcp                          # Start server with STDIO transport
        ddgs-mcp --http                   # Start server with HTTP transport
        ddgs-mcp --http --port 8080       # Start HTTP server on custom port
        ddgs-mcp --verbose                # Start with verbose logging
    """
    # Configure logging if verbose mode is enabled
    if verbose:
        import logging

        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger(__name__)
        logger.info("Starting DDGS MCP Server with verbose logging")

        # Show configuration info
        logger.info("DDGS client initialized")

        if http:
            logger.info(f"Starting HTTP transport on {host}:{port}")
        else:
            logger.info("Starting STDIO transport")

    # Start the server with specified transport
    if http:
        mcp.run(transport="http", host=host, port=port, show_banner=False)
    else:
        mcp.run(show_banner=False)


# Information command
@app.command()
def info() -> None:
    """Display detailed information about the DDGS MCP server."""
    print("""
🔍 DDGS MCP Server Information

Server Configuration:
  • Name: DDGS-MCP-Server
  • Transport: STDIO (default) or HTTP
  • Default HTTP Port: 10090

Available Tools:
  • web_search: Web search across multiple search engines
    - Parameters: query, region, max_results, timelimit, backend
    - Backends: Google, Bing, Brave, DuckDuckGo, and more

  • news_search: News search with time-based filtering
    - Parameters: query, region, max_results, timelimit, backend
    - Backends: Bing, DuckDuckGo, Yahoo

Available Resources:
  • search://web/{query} - Web search results as JSON
  • search://news/{query}{?timelimit} - News search results as JSON

Examples:
  • ddgs-mcp                    # Start with STDIO transport
  • ddgs-mcp --http             # Start with HTTP transport
  • ddgs-mcp info               # Show this information
  • ddgs-mcp --help             # Show command help
""")


# Entry point function for the project configuration
def cli_main() -> None:
    """Entry point for the ddgs-mcp command."""
    import sys

    # Check if info command is requested and handle it directly
    if len(sys.argv) > 1 and sys.argv[1] == "info":
        show_info()
        return

    app()


def show_info() -> None:
    """Display detailed information about the DDGS MCP server."""
    print("""
🔍 DDGS MCP Server Information

Server Configuration:
  • Name: DDGS-MCP-Server
  • Transport: STDIO (default) or HTTP
  • Default HTTP Port: 10090

Available Tools:
  • web_search: Web search across multiple search engines
    - Parameters: query, region, max_results, timelimit, backend
    - Backends: Google, Bing, Brave, DuckDuckGo, and more

  • news_search: News search with time-based filtering
    - Parameters: query, region, max_results, timelimit, backend
    - Backends: Bing, DuckDuckGo, Yahoo

Available Resources:
  • search://web/{query} - Web search results as JSON
  • search://news/{query}{?timelimit} - News search results as JSON

Examples:
  • ddgs-mcp                    # Start with STDIO transport
  • ddgs-mcp --http             # Start with HTTP transport
  • ddgs-mcp info               # Show this information
  • ddgs-mcp --help             # Show command help
""")


if __name__ == "__main__":
    cli_main()
