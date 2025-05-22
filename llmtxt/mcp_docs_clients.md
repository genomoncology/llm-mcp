## Writing MCP Clients

The SDK provides a high-level client interface for connecting to MCP servers
using
various [transports](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports):

```python
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client

# Create server parameters for stdio connection
server_params = StdioServerParameters(
    command="python",  # Executable
    args=["example_server.py"],  # Optional command line arguments
    env=None,  # Optional environment variables
)


# Optional: create a sampling callback
async def handle_sampling_message(
        message: types.CreateMessageRequestParams,
) -> types.CreateMessageResult:
    return types.CreateMessageResult(
        role="assistant",
        content=types.TextContent(
            type="text",
            text="Hello, world! from model",
        ),
        model="gpt-3.5-turbo",
        stopReason="endTurn",
    )


async def run():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(
                read, write, sampling_callback=handle_sampling_message
        ) as session:
            # Initialize the connection
            await session.initialize()

            # List available prompts
            prompts = await session.list_prompts()

            # Get a prompt
            prompt = await session.get_prompt(
                "example-prompt", arguments={"arg1": "value"}
            )

            # List available resources
            resources = await session.list_resources()

            # List available tools
            tools = await session.list_tools()

            # Read a resource
            content, mime_type = await session.read_resource(
                "file://some/path")

            # Call a tool
            result = await session.call_tool("tool-name",
                                             arguments={"arg1": "value"})


if __name__ == "__main__":
    import asyncio

    asyncio.run(run())
```

Clients can also connect
using [Streamable HTTP transport](https://modelcontextprotocol.io/specification/2025-03-26/basic/transports#streamable-http):

```python
from mcp.client.streamable_http import streamablehttp_client
from mcp import ClientSession


async def main():
    # Connect to a streamable HTTP server
    async with streamablehttp_client("example/mcp") as (
            read_stream,
            write_stream,
            _,
    ):
        # Create a session using the client streams
        async with ClientSession(read_stream, write_stream) as session:
            # Initialize the connection
            await session.initialize()
            # Call a tool
            tool_result = await session.call_tool("echo", {"message": "hello"})
```

### OAuth Authentication for Clients

The SDK
includes [authorization support](https://modelcontextprotocol.io/specification/2025-03-26/basic/authorization)
for connecting to protected MCP servers:

```python
from mcp.client.auth import OAuthClientProvider, TokenStorage
from mcp.client.session import ClientSession
from mcp.client.streamable_http import streamablehttp_client
from mcp.shared.auth import OAuthClientInformationFull, OAuthClientMetadata,
    OAuthToken


class CustomTokenStorage(TokenStorage):
    """Simple in-memory token storage implementation."""

    async def get_tokens(self) -> OAuthToken | None:
        pass

    async def set_tokens(self, tokens: OAuthToken) -> None:
        pass

    async def get_client_info(self) -> OAuthClientInformationFull | None:
        pass

    async def set_client_info(self,
                              client_info: OAuthClientInformationFull) -> None:
        pass


async def main():
    # Set up OAuth authentication
    oauth_auth = OAuthClientProvider(
        server_url="https://api.example.com",
        client_metadata=OAuthClientMetadata(
            client_name="My Client",
            redirect_uris=["http://localhost:3000/callback"],
            grant_types=["authorization_code", "refresh_token"],
            response_types=["code"],
        ),
        storage=CustomTokenStorage(),
        redirect_handler=lambda url: print(f"Visit: {url}"),
        callback_handler=lambda: ("auth_code", None),
    )

    # Use with streamable HTTP client
    async with streamablehttp_client(
            "https://api.example.com/mcp", auth=oauth_auth
    ) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            # Authenticated session ready
```

For a complete working example, see [
`examples/clients/simple-auth-client/`](examples/clients/simple-auth-client/).

### MCP Primitives

The MCP protocol defines three core primitives that servers can implement:

| Primitive | Control                | Description                                       | Example Use                  |
|-----------|------------------------|---------------------------------------------------|------------------------------|
| Prompts   | User-controlled        | Interactive templates invoked by user choice      | Slash commands, menu options |
| Resources | Application-controlled | Contextual data managed by the client application | File contents, API responses |
| Tools     | Model-controlled       | Functions exposed to the LLM to take actions      | API calls, data updates      |

### Server Capabilities

MCP servers declare capabilities during initialization:

| Capability   | Feature Flag                  | Description                     |
|--------------|-------------------------------|---------------------------------|
| `prompts`    | `listChanged`                 | Prompt template management      |
| `resources`  | `subscribe`<br/>`listChanged` | Resource exposure and updates   |
| `tools`      | `listChanged`                 | Tool discovery and execution    |
| `logging`    | -                             | Server logging configuration    |
| `completion` | -                             | Argument completion suggestions |
