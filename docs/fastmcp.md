# FastMCP

FastMCP is the standard framework for building Model Context Protocol (MCP) applications in Python. MCP provides a standardized way to connect Large Language Models (LLMs) to tools and data, and FastMCP makes it production-ready with clean, Pythonic code. FastMCP pioneered Python MCP development with FastMCP 1.0 being incorporated into the official MCP SDK in 2024. FastMCP 2.0 extends far beyond basic protocol implementation, delivering everything needed for production including advanced MCP patterns (server composition, proxying, OpenAPI/FastAPI generation, tool transformation), enterprise authentication (Google, GitHub, Azure, Auth0, WorkOS), deployment tools, testing frameworks, and comprehensive client libraries.

The framework handles all complex protocol details automatically, allowing developers to focus on building functionality. In most cases, decorating a Python function is all that's needed - FastMCP handles schema generation, parameter validation, error handling, and transport management. FastMCP servers can expose data through Resources, provide functionality through Tools, and define interaction patterns through Prompts. The framework supports both synchronous and asynchronous functions, provides built-in support for all Pydantic types, and includes automatic JSON schema generation for parameters and return values.

## APIs and Key Functions

### Creating a FastMCP Server

A FastMCP server is the core container for tools, resources, and prompts that expose functionality to MCP clients.

```python
from fastmcp import FastMCP

# Create a basic server
mcp = FastMCP(name="MyAssistantServer")

# Create a server with instructions
mcp_with_instructions = FastMCP(
    name="HelpfulAssistant",
    instructions="This server provides data analysis tools. Call get_average() to analyze numerical data.",
)

# Create a server with authentication
from fastmcp.server.auth.providers import BearerTokenProvider

mcp_secure = FastMCP(
    name="SecureServer",
    auth=BearerTokenProvider(token="your-secret-token"),
    mask_error_details=True,
    include_tags={"public"},
    exclude_tags={"internal", "deprecated"}
)
```

### Defining Tools with @tool Decorator

Tools are Python functions that LLMs can execute to perform actions, query systems, or access data.

```python
from fastmcp import FastMCP
from typing import Annotated
from pydantic import Field

mcp = FastMCP(name="CalculatorServer")

# Basic tool with type annotations
@mcp.tool
def add(a: int, b: int) -> int:
    """Adds two integer numbers together."""
    return a + b

# Tool with field validation and metadata
@mcp.tool(
    name="search_products",
    description="Search the product catalog with optional category filtering.",
    tags={"catalog", "search"},
    annotations={
        "readOnlyHint": True,
        "openWorldHint": False
    }
)
def search_products(
    query: Annotated[str, Field(description="Search query string")],
    category: Annotated[str | None, Field(description="Product category")] = None,
    max_results: Annotated[int, Field(ge=1, le=100)] = 10
) -> list[dict]:
    """Search for products in the catalog."""
    results = [
        {"id": 1, "name": "Product A", "category": category or "general"},
        {"id": 2, "name": "Product B", "category": category or "general"}
    ]
    return results[:max_results]

# Tool with context access for logging and progress
from fastmcp import Context

@mcp.tool
async def process_data(data_uri: str, ctx: Context) -> dict:
    """Process data from a resource with progress reporting."""
    await ctx.info(f"Processing data from {data_uri}")

    resource = await ctx.read_resource(data_uri)
    data = resource[0].text if resource else ""

    await ctx.report_progress(progress=50, total=100)

    summary = await ctx.sample(f"Summarize this in 10 words: {data[:200]}")

    await ctx.report_progress(progress=100, total=100)
    return {"length": len(data), "summary": summary.text}
```

### Defining Resources with @resource Decorator

Resources provide read-only access to data for LLMs, either as static content or dynamically generated based on parameters.

```python
from fastmcp import FastMCP, Context
from pathlib import Path
import aiofiles

mcp = FastMCP(name="DataServer")

# Basic static resource
@mcp.resource("resource://greeting")
def get_greeting() -> str:
    """Provides a simple greeting message."""
    return "Hello from FastMCP Resources!"

# Resource returning JSON data
@mcp.resource(
    uri="data://config",
    name="ApplicationConfig",
    description="Provides application configuration as JSON.",
    mime_type="application/json",
    tags={"config", "settings"},
    annotations={"readOnlyHint": True, "idempotentHint": True}
)
def get_config() -> dict:
    """Get application configuration."""
    return {
        "theme": "dark",
        "version": "1.2.0",
        "features": ["tools", "resources"],
    }

# Async resource with file reading
@mcp.resource("file:///app/data/log.txt", mime_type="text/plain")
async def read_log() -> str:
    """Reads content from a log file asynchronously."""
    try:
        async with aiofiles.open("/app/data/log.txt", mode="r") as f:
            return await f.read()
    except FileNotFoundError:
        return "Log file not found."

# Resource template with URI parameters
@mcp.resource("weather://{city}/current")
def get_weather(city: str) -> dict:
    """Provides weather information for a specific city."""
    return {
        "city": city.capitalize(),
        "temperature": 22,
        "condition": "Sunny",
        "unit": "celsius"
    }

# Resource template with wildcard parameters
@mcp.resource("path://{filepath*}")
def get_path_content(filepath: str) -> str:
    """Retrieves content at a specific path."""
    return f"Content at path: {filepath}"

# Resource template with query parameters
@mcp.resource("data://{id}{?format,version}")
def get_data(id: str, format: str = "json", version: int = 1) -> str:
    """Retrieve data in specified format."""
    if format == "xml":
        return f"<data id='{id}' version='{version}' />"
    return f'{{"id": "{id}", "version": {version}}}'
```

### Defining Prompts with @prompt Decorator

Prompts are reusable message templates that help LLMs generate structured, purposeful responses.

```python
from fastmcp import FastMCP, Context
from fastmcp.prompts.prompt import Message, PromptMessage, TextContent
from pydantic import Field

mcp = FastMCP(name="PromptServer")

# Basic prompt returning a string
@mcp.prompt
def ask_about_topic(topic: str) -> str:
    """Generates a user message asking for an explanation of a topic."""
    return f"Can you please explain the concept of '{topic}'?"

# Prompt with field validation
@mcp.prompt(
    name="analyze_data_request",
    description="Creates a request to analyze data with specific parameters",
    tags={"analysis", "data"}
)
def data_analysis_prompt(
    data_uri: str = Field(description="The URI of the resource containing the data."),
    analysis_type: str = Field(default="summary", description="Type of analysis.")
) -> str:
    """Generate data analysis request."""
    return f"Please perform a '{analysis_type}' analysis on the data found at {data_uri}."

# Prompt returning multiple messages
@mcp.prompt
def roleplay_scenario(character: str, situation: str) -> list:
    """Sets up a roleplaying scenario with initial messages."""
    return [
        Message(f"Let's roleplay. You are {character}. The situation is: {situation}"),
        Message("Okay, I understand. I am ready. What happens next?", role="assistant")
    ]

# Async prompt with context
@mcp.prompt
async def generate_report_request(report_type: str, ctx: Context) -> str:
    """Generates a request for a report with request tracking."""
    return f"Please create a {report_type} report. Request ID: {ctx.request_id}"

# Prompt with complex type arguments (auto-converted from JSON strings)
@mcp.prompt
def analyze_data(
    numbers: list[int],
    metadata: dict[str, str],
    threshold: float
) -> str:
    """Analyze numerical data."""
    avg = sum(numbers) / len(numbers)
    return f"Average: {avg}, above threshold: {avg > threshold}"
```

### Running a FastMCP Server

Start your FastMCP server with different transport protocols for various deployment scenarios.

```python
from fastmcp import FastMCP
import asyncio

mcp = FastMCP(name="MyServer")

@mcp.tool
def hello(name: str) -> str:
    """Greet a user by name."""
    return f"Hello, {name}!"

# STDIO transport (default, for local tools like Claude Desktop)
if __name__ == "__main__":
    mcp.run()

# HTTP transport (for web services and remote access)
if __name__ == "__main__":
    mcp.run(transport="http", host="127.0.0.1", port=8000)
    # Server accessible at http://localhost:8000/mcp/

# SSE transport (legacy, use HTTP instead)
if __name__ == "__main__":
    mcp.run(transport="sse", host="127.0.0.1", port=8000)

# Async usage with run_async()
async def main():
    await mcp.run_async(transport="http", port=8000)

if __name__ == "__main__":
    asyncio.run(main())

# Custom routes alongside MCP endpoint
from starlette.requests import Request
from starlette.responses import PlainTextResponse

@mcp.custom_route("/health", methods=["GET"])
async def health_check(request: Request) -> PlainTextResponse:
    return PlainTextResponse("OK")

if __name__ == "__main__":
    mcp.run(transport="http")
    # Health check at http://localhost:8000/health
    # MCP endpoint at http://localhost:8000/mcp/
```

### Creating a FastMCP Client

The FastMCP Client provides a programmatic interface for interacting with MCP servers.

```python
import asyncio
from fastmcp import Client, FastMCP

# In-memory server (ideal for testing)
server = FastMCP("TestServer")

@server.tool
def add(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

client = Client(server)

# HTTP server
client_http = Client("https://example.com/mcp")

# Local Python script
client_script = Client("my_mcp_server.py")

# Basic client usage
async def main():
    async with client:
        # Check connectivity
        await client.ping()

        # List available operations
        tools = await client.list_tools()
        print(f"Available tools: {[t.name for t in tools.tools]}")

        resources = await client.list_resources()
        print(f"Available resources: {[r.uri for r in resources.resources]}")

        prompts = await client.list_prompts()
        print(f"Available prompts: {[p.name for p in prompts.prompts]}")

        # Execute tool
        result = await client.call_tool("add", {"a": 5, "b": 3})
        print(f"Tool result: {result.data}")  # 8

        # Read resource
        content = await client.read_resource("file:///config/settings.json")
        print(f"Resource content: {content[0].text}")

        # Get prompt
        messages = await client.get_prompt("analyze_data", {"data": [1, 2, 3]})
        print(f"Prompt messages: {messages.messages}")

asyncio.run(main())
```

### Multi-Server Client Configuration

Connect to multiple MCP servers simultaneously using configuration dictionaries.

```python
import asyncio
from fastmcp import Client

# Configuration for multiple servers
config = {
    "mcpServers": {
        "weather": {
            "transport": "http",
            "url": "https://weather-api.example.com/mcp",
            "headers": {"Authorization": "Bearer token123"},
        },
        "assistant": {
            "transport": "stdio",
            "command": "python",
            "args": ["./assistant_server.py", "--verbose"],
            "env": {"DEBUG": "true"},
            "cwd": "/path/to/server",
        },
        "database": {
            "command": "uvx",
            "args": ["--from", "mcp-server-postgres", "mcp-server-postgres", "--database", "mydb"]
        }
    }
}

client = Client(config)

async def main():
    async with client:
        # Tools are prefixed with server names
        weather_data = await client.call_tool(
            "weather_get_forecast",
            {"city": "London"}
        )
        print(f"Weather: {weather_data.data}")

        response = await client.call_tool(
            "assistant_answer_question",
            {"question": "What's the capital of France?"}
        )
        print(f"Answer: {response.data}")

        # Resources use prefixed URIs
        icons = await client.read_resource("weather://weather/icons/sunny")
        templates = await client.read_resource("resource://assistant/templates/list")

asyncio.run(main())
```

### Client with Callback Handlers

Configure client handlers for logging, progress monitoring, and LLM sampling.

```python
import asyncio
from fastmcp import Client
from fastmcp.client.logging import LogMessage

async def log_handler(message: LogMessage):
    """Handle server log messages."""
    print(f"Server log [{message.level}]: {message.data}")

async def progress_handler(progress: float, total: float | None, message: str | None):
    """Monitor long-running operations."""
    percentage = (progress / total * 100) if total else 0
    print(f"Progress: {percentage:.1f}% - {message}")

async def sampling_handler(messages, params, context):
    """Respond to server LLM requests."""
    # Integrate with your LLM service here
    return "Generated response from LLM"

client = Client(
    "https://api.example.com/mcp",
    log_handler=log_handler,
    progress_handler=progress_handler,
    sampling_handler=sampling_handler,
    timeout=30.0
)

async def main():
    async with client:
        result = await client.call_tool("process_data", {"uri": "data://large-file"})
        # Progress updates will be printed as the tool executes
        print(f"Final result: {result.data}")

asyncio.run(main())
```

### Server Composition with mount() and import_server()

Combine multiple FastMCP servers into a single application for better organization.

```python
from fastmcp import FastMCP
import asyncio

# Create main server
main = FastMCP(name="MainServer")

# Create subservers with specific functionality
weather = FastMCP(name="WeatherService")
database = FastMCP(name="DatabaseService")

@weather.tool
def get_forecast(city: str) -> dict:
    """Get weather forecast for a city."""
    return {"city": city, "temp": 22, "condition": "Sunny"}

@database.tool
def query_users(email: str) -> dict:
    """Query user database by email."""
    return {"email": email, "name": "Alice", "active": True}

# Mount servers with prefixes
main.mount(weather, prefix="weather")
main.mount(database, prefix="db")

# Tools are now accessible as:
# - weather_get_forecast
# - db_query_users

async def main_async():
    async with main.run_async(transport="http", port=8000):
        print("Composed server running at http://localhost:8000/mcp/")
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main_async())
```

### Proxy Server Pattern

Use FastMCP to act as a proxy for other MCP servers, bridging transports or adding functionality.

```python
from fastmcp import FastMCP, Client
import asyncio

# Backend server (could be remote SSE, stdio, etc.)
backend = Client("https://remote-server.example.com/mcp/sse")

# Create proxy server that exposes backend via HTTP
proxy = FastMCP.as_proxy(
    backend,
    name="ProxyServer",
    instructions="This is a proxy to the remote server."
)

# Add custom middleware or authentication to the proxy
@proxy.tool
def proxy_info() -> dict:
    """Get information about this proxy."""
    return {"type": "proxy", "backend": "remote-server.example.com"}

async def main():
    # Run proxy locally via HTTP
    await proxy.run_async(transport="http", port=8000)

if __name__ == "__main__":
    asyncio.run(main())
```

### OpenAPI Integration

Generate MCP servers from OpenAPI specifications or FastAPI applications.

```python
import httpx
from fastmcp import FastMCP
from fastapi import FastAPI

# From OpenAPI spec
spec = httpx.get("https://api.example.com/openapi.json").json()
mcp_from_spec = FastMCP.from_openapi(
    openapi_spec=spec,
    client=httpx.AsyncClient(),
    name="APIServer"
)

# From FastAPI app
app = FastAPI()

@app.get("/users/{user_id}")
def get_user(user_id: int):
    """Get user by ID."""
    return {"id": user_id, "name": "Alice"}

@app.post("/users")
def create_user(name: str, email: str):
    """Create a new user."""
    return {"id": 1, "name": name, "email": email}

# Convert FastAPI app to MCP server
mcp_from_fastapi = FastMCP.from_fastapi(
    app=app,
    name="FastAPIServer"
)

# Run the converted server
if __name__ == "__main__":
    mcp_from_fastapi.run(transport="http", port=8000)
```

### Using FastMCP CLI

Run FastMCP servers with automatic dependency management and configuration.

```bash
# Basic usage
fastmcp run server.py

# With specific Python version
fastmcp run server.py --python 3.11

# With additional packages
fastmcp run server.py --with pandas --with numpy

# With requirements file
fastmcp run server.py --with-requirements requirements.txt

# With specific transport
fastmcp run server.py --transport http --port 8000

# Pass arguments to server
fastmcp run config_server.py -- --config config.json --debug

# Development mode with MCP Inspector
fastmcp dev server.py

# Install in Claude Desktop
fastmcp install claude-desktop server.py

# Install in Claude Code
fastmcp install claude-code server.py

# Generate MCP configuration
fastmcp install mcp-json server.py --output config.json
```

### Authentication with OAuth Providers

Secure FastMCP servers with OAuth 2.1 authentication using various identity providers.

```python
from fastmcp import FastMCP
from fastmcp.server.auth.providers import (
    GitHubOAuthProvider,
    GoogleOAuthProvider,
    AzureOAuthProvider,
    Auth0OAuthProvider,
)

# GitHub OAuth
mcp_github = FastMCP(
    name="GitHubSecureServer",
    auth=GitHubOAuthProvider(
        client_id="your-github-client-id",
        client_secret="your-github-client-secret",
    )
)

# Google OAuth
mcp_google = FastMCP(
    name="GoogleSecureServer",
    auth=GoogleOAuthProvider(
        client_id="your-google-client-id.apps.googleusercontent.com",
        client_secret="your-google-client-secret",
    )
)

# Azure/Microsoft Entra OAuth
mcp_azure = FastMCP(
    name="AzureSecureServer",
    auth=AzureOAuthProvider(
        client_id="your-azure-client-id",
        client_secret="your-azure-client-secret",
        tenant_id="your-tenant-id",
    )
)

# Auth0 OAuth
mcp_auth0 = FastMCP(
    name="Auth0SecureServer",
    auth=Auth0OAuthProvider(
        client_id="your-auth0-client-id",
        client_secret="your-auth0-client-secret",
        domain="your-domain.auth0.com",
    )
)

@mcp_github.tool
def secure_operation() -> str:
    """This operation requires GitHub authentication."""
    return "Authenticated successfully!"

if __name__ == "__main__":
    mcp_github.run(transport="http", port=8000)
```

### Token Verification for External Auth

Validate bearer tokens issued by external authentication systems.

```python
from fastmcp import FastMCP
from fastmcp.server.auth.providers import JWTVerifier
import jwt

# JWT token verification
mcp = FastMCP(
    name="SecureServer",
    auth=JWTVerifier(
        secret="your-jwt-secret",
        algorithm="HS256",
        audience="your-api",
        issuer="your-auth-service"
    )
)

@mcp.tool
def protected_data() -> dict:
    """Access protected data with valid JWT."""
    return {"data": "sensitive information"}

# Custom token verification
from fastmcp.server.auth import TokenVerifier

class CustomTokenVerifier(TokenVerifier):
    async def verify_token(self, token: str) -> dict:
        """Custom token verification logic."""
        # Check token against your database/service
        if token == "valid-token-12345":
            return {"user_id": "user123", "scopes": ["read", "write"]}
        raise ValueError("Invalid token")

mcp_custom = FastMCP(
    name="CustomAuthServer",
    auth=CustomTokenVerifier()
)

if __name__ == "__main__":
    mcp.run(transport="http", port=8000)
```

## Summary

FastMCP provides a comprehensive, production-ready framework for building Model Context Protocol applications in Python. The framework's decorator-based API (@tool, @resource, @prompt) makes it simple to expose Python functions as MCP capabilities while automatically handling schema generation, validation, and error handling. FastMCP supports both synchronous and asynchronous operations, all Pydantic types, and provides full control over parameter validation through Field constraints. The framework's automatic type coercion ensures that data from MCP clients is properly validated and converted to the expected Python types.

FastMCP's flexibility extends to deployment and integration scenarios. Servers can run with STDIO transport for local tools like Claude Desktop, HTTP transport for web services and remote access, or be embedded in existing ASGI/FastAPI applications. The framework includes robust authentication options (OAuth 2.1 with GitHub, Google, Azure, Auth0, plus custom token verification), server composition capabilities for building modular applications, and proxy patterns for bridging different transports. The FastMCP Client provides a programmatic interface for testing and building applications that interact with MCP servers, with support for multi-server configurations, callback handlers for logging and progress monitoring, and automatic transport selection. Combined with the FastMCP CLI for dependency management and development workflows, FastMCP provides the complete toolkit for building, testing, deploying, and securing production MCP applications.
