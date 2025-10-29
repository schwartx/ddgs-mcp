# DDGS-MCP

MCP server of [DDGS](https://github.com/deedy5/ddgs) - metasearch capabilities via Model Context Protocol.

## Acknowledgments

This project is built upon the excellent [DDGS](https://github.com/deedy5/ddgs) library by deedy5. Thank you for creating and maintaining this powerful metasearch library!


## Quick Start

### Installation
```bash
uv sync
uv pip install -e .
```

### Usage
```bash
# Run with STDIO transport (default)
ddgs-mcp

# Run with HTTP transport
ddgs-mcp --http
```

### Claude Code Integration

```
 claude mcp add -s local -t http web-search-ddgs http://127.0.0.1:10090
```

## Available Tools

- `web_search`: Web search across multiple engines
- `news_search`: News search with time filtering

## Available Resources

- `search://web/{query}`: Web search results as JSON
- `search://news/{query}{?timelimit}`: News search results as JSON

## Environment Variables

- `DDGS_HTTP_PROXY`: HTTP proxy URL (e.g., `http://127.0.0.1:7890`)
