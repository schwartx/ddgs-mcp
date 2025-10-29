"""
DDGS MCP Server - A metasearch MCP server using DDGS library.

This server provides comprehensive search capabilities through the Model Context Protocol,
integrating DDGS (Dux Distributed Global Search) with FastMCP framework.
"""

import json
from typing import Annotated, Optional, Dict, Any
from pydantic import Field

from fastmcp import FastMCP
from ddgs import DDGS

# Initialize the FastMCP server
mcp = FastMCP(
    name="DDGS-MCP-Server",
    instructions="Metasearch server providing web, news search capabilities through DDGS library integration. Offers comprehensive search tools, resource templates, and research prompts.",
)

# Initialize DDGS client
_ddgs_client = DDGS()


@mcp.tool
def web_search(
    query: Annotated[str, Field(description="Search query string")],
    region: Annotated[
        str, Field(default="us-en", description="Region code (e.g., us-en, cn-zh)")
    ],
    max_results: Annotated[
        int, Field(default=10, ge=1, le=100, description="Maximum number of results")
    ],
    safesearch: Annotated[
        str,
        Field(default="moderate", description="Safe search level: on, moderate, off"),
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
            safesearch=safesearch,
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


# Prompts
@mcp.prompt
def research_prompt(topic: str) -> str:
    """
    Generate a comprehensive research prompt with current web information.

    This prompt performs a quick search to provide context for research on the given topic.
    """
    try:
        # Quick search for context
        results = _ddgs_client.text(topic, max_results=3, safesearch="moderate")
        context = ""
        if results:
            context = "\n".join(
                [
                    f"- {r.get('title', 'No title')}: {r.get('body', '')[:200]}..."
                    for r in results
                ]
            )

        return f"""Research Analysis Request

Topic: {topic}

Recent Context:
{context if context else "No recent context found."}

Please provide a comprehensive analysis of this topic, including:

1. **Current State**: What is the current situation or understanding?
2. **Key Developments**: What recent changes or events are relevant?
3. **Important Factors**: What are the critical elements or considerations?
4. **Future Implications**: What might be the future trends or consequences?
5. **Knowledge Gaps**: What important information might be missing?

Base your analysis on the provided context and your knowledge, focusing on accuracy and relevance.
"""
    except Exception as e:
        return f"""Research Analysis Request

Topic: {topic}

Note: Unable to fetch recent context due to: {e}

Please provide a comprehensive analysis of this topic based on your knowledge.
"""


@mcp.prompt
def competitive_analysis_prompt(company_or_product: str) -> str:
    """
    Generate a competitive analysis prompt with market information.
    """
    try:
        # Search for company/product and competitors
        results = _ddgs_client.text(
            f"{company_or_product} competitors analysis", max_results=3
        )
        context = ""
        if results:
            context = "\n".join(
                [
                    f"- {r.get('title', 'No title')}: {r.get('body', '')[:200]}..."
                    for r in results
                ]
            )

        return f"""Competitive Analysis Request

Subject: {company_or_product}

Market Context:
{context if context else "No market context found."}

Please provide a thorough competitive analysis including:

1. **Market Position**: Where does this company/product stand in the market?
2. **Key Competitors**: Who are the main competitors and what are their strengths?
3. **Competitive Advantages**: What makes this company/product unique?
4. **Market Trends**: What trends are affecting this market segment?
5. **Strategic Recommendations**: What strategies could improve competitive position?

Focus on actionable insights and realistic assessments.
"""
    except Exception as e:
        return f"""Competitive Analysis Request

Subject: {company_or_product}

Note: Unable to fetch market context due to: {e}

Please provide a competitive analysis based on your knowledge.
"""


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

Available Tools:
    - web_search: Web search across multiple engines
    - news_search: News search with time filtering

Available Resources:
    - search://web/{query}
    - search://news/{query}{?timelimit}

Available Prompts:
    - research_prompt: Comprehensive research analysis
    - competitive_analysis_prompt: Market competitive analysis
""")
        return

    # Check for HTTP transport
    if "--http" in sys.argv:
        print("Starting DDGS MCP Server with HTTP transport on port 8000...")
        print("MCP endpoint: http://localhost:8000/mcp/")
        mcp.run(transport="http", host="127.0.0.1", port=8000)
    else:
        print("Starting DDGS MCP Server with STDIO transport...")
        mcp.run()


if __name__ == "__main__":
    main()
