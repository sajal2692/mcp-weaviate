# MCP Server for Weaviate - Implementation Plan

## Overview
Build a Model Context Protocol (MCP) server for Weaviate using FastMCP that provides comprehensive search and data management capabilities for LLMs to interact with Weaviate vector databases.

## Architecture

### Technology Stack
- **Framework**: FastMCP 2.0+
- **Vector Database**: Weaviate
- **Language**: Python 3.12+
- **Package Manager**: UV (with NPX support via Smithery)
- **Deployment**: Smithery-compatible for cross-platform distribution

## Implementation Steps

### 1. Project Structure
```
mcp-weaviate/
├── src/
│   ├── __init__.py
│   ├── main.py           # Main server entry point
│   ├── config.py         # Configuration management
│   ├── weaviate_client.py # Weaviate client wrapper
│   └── tools.py          # MCP tool implementations
├── tests/
│   ├── __init__.py
│   ├── test_tools.py
│   └── test_client.py
├── pyproject.toml        # Python project configuration
├── smithery.yaml         # Smithery deployment config
├── README.md             # Documentation
├── LICENSE
└── .env.example          # Environment variables template
```

### 2. Core Dependencies

Update `pyproject.toml`:
```toml
[project]
name = "mcp-weaviate"
version = "0.1.0"
description = "MCP server for Weaviate vector database operations"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "fastmcp>=2.11.3",
    "weaviate-client>=4.0.0",
    "click>=8.0.0",
    "python-dotenv>=1.0.0",
    "pydantic>=2.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-asyncio>=0.21.0",
    "pytest-mock>=3.0.0",
]

[project.scripts]
mcp-weaviate = "src.main:cli"
```

### 3. Configuration Management

`src/config.py`:
- Environment variable parsing with python-dotenv
- CLI argument handling with Click decorators
- Configuration validation with Pydantic dataclasses
- Support for both local and cloud Weaviate connections
- Multiple authentication methods:
  - API Key authentication
  - Anonymous access for local development
  - Third-party API keys (Cohere, OpenAI, etc.)

Enhanced configuration options:
```python
@dataclass
class WeaviateConfig:
    # Connection type
    connection_type: str = "local"              # "local" or "cloud"

    # Local connection parameters
    host: str = "localhost"                     # Local host
    port: int = 8080                           # HTTP port
    grpc_port: int = 50051                     # gRPC port for faster operations

    # Cloud connection parameters
    cluster_url: Optional[str] = None          # WCS cluster URL

    # Authentication
    api_key: Optional[str] = None              # Weaviate API key

    # Additional configuration
    timeout_init: int = 30                     # Initialization timeout
    timeout_query: int = 60                    # Query timeout
    timeout_insert: int = 120                  # Insert timeout
    additional_headers: Dict[str, str] = field(default_factory=dict)  # Custom headers
    startup_period: int = 5                    # Connection retry period

    # Third-party API keys
    cohere_api_key: Optional[str] = None       # For Cohere integration
    openai_api_key: Optional[str] = None       # For OpenAI integration
```

### 4. Weaviate Client Wrapper

`src/weaviate_client.py`:
```python
class WeaviateClientManager:
    """Wrapper for Weaviate operations with connection management"""

    def __init__(self, config: WeaviateConfig):
        self.config = config
        self.client = None
        self._connected = False

    async def connect(self):
        """Establish connection to Weaviate based on configuration"""
        if self.config.connection_type == "local":
            # Local connection with optional authentication
            additional_config = AdditionalConfig(
                timeout=Timeout(
                    init=self.config.timeout_init,
                    query=self.config.timeout_query,
                    insert=self.config.timeout_insert
                )
            )

            auth_credentials = None
            if self.config.api_key:
                auth_credentials = Auth.api_key(self.config.api_key)

            self.client = weaviate.connect_to_local(
                host=self.config.host,
                port=self.config.port,
                grpc_port=self.config.grpc_port,
                auth_credentials=auth_credentials,
                headers=self.config.additional_headers,
                additional_config=additional_config
            )

        elif self.config.connection_type == "cloud":
            # Cloud connection (Weaviate Cloud Services)
            if not self.config.cluster_url or not self.config.api_key:
                raise ValueError("cluster_url and api_key required for cloud connection")

            additional_config = AdditionalConfig(
                timeout=Timeout(
                    init=self.config.timeout_init,
                    query=self.config.timeout_query,
                    insert=self.config.timeout_insert
                )
            )

            self.client = weaviate.connect_to_weaviate_cloud(
                cluster_url=self.config.cluster_url,
                auth_credentials=Auth.api_key(self.config.api_key),
                headers=self.config.additional_headers,
                additional_config=additional_config
            )

        # Test connection
        if not self.client.is_ready():
            raise ConnectionError("Failed to establish connection to Weaviate")

        self._connected = True

    async def disconnect(self):
        """Clean up connections"""
        if self.client:
            self.client.close()
            self._connected = False

    def is_connected(self) -> bool:
        """Check if client is connected"""
        return self._connected and self.client and self.client.is_ready()

    # Context manager support
    async def __aenter__(self):
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.disconnect()
```

### 5. MCP Tools Implementation

`src/tools.py` - Core tools to implement:

#### Search Tools
```python
@mcp.tool
async def search_objects(
    class_name: str,
    query: Optional[str] = None,
    vector: Optional[List[float]] = None,
    limit: int = 10,
    where_filter: Optional[Dict] = None,
    properties: Optional[List[str]] = None,
    search_type: str = "hybrid"  # "vector", "keyword", "hybrid"
) -> Dict:
    """Search for objects in Weaviate using vector, keyword, or hybrid search"""
    pass

@mcp.tool
async def search_similar(
    class_name: str,
    object_id: str,
    limit: int = 10,
    distance: float = 0.5
) -> List[Dict]:
    """Find objects similar to a given object"""
    pass
```

#### Schema Tools
```python
@mcp.tool
async def list_classes() -> List[str]:
    """List all available Weaviate classes"""
    pass

@mcp.tool
async def get_schema(
    class_name: Optional[str] = None
) -> Dict:
    """Get schema information for all classes or a specific class"""
    pass

@mcp.tool
async def get_class_properties(
    class_name: str
) -> List[Dict]:
    """Get properties defined for a specific class"""
    pass
```

#### Data Management Tools
```python
@mcp.tool
async def get_object(
    class_name: str,
    object_id: str,
    properties: Optional[List[str]] = None
) -> Dict:
    """Retrieve a specific object by ID"""
    pass

@mcp.tool
async def aggregate_data(
    class_name: str,
    group_by: Optional[List[str]] = None,
    metrics: List[str] = ["count"]  # count, sum, mean, max, min
) -> Dict:
    """Perform aggregation queries on Weaviate data"""
    pass

@mcp.tool
async def batch_import(
    class_name: str,
    objects: List[Dict],
    batch_size: int = 100
) -> Dict:
    """Import multiple objects in batch"""
    pass

@mcp.tool
async def delete_objects(
    class_name: str,
    where_filter: Dict
) -> Dict:
    """Delete objects matching the filter criteria"""
    pass
```

#### Utility Tools
```python
@mcp.tool
async def check_connection() -> Dict:
    """Check Weaviate connection status and return cluster info"""
    pass

@mcp.tool
async def get_statistics(
    class_name: Optional[str] = None
) -> Dict:
    """Get database statistics (object counts, index status, etc.)"""
    pass
```

### 6. Main Server Entry Point

`src/main.py`:
```python
import asyncio
import click
from fastmcp import FastMCP
from src.config import WeaviateConfig
from src.weaviate_client import WeaviateClientManager
from src.tools import register_tools

# Initialize FastMCP server
mcp = FastMCP("Weaviate MCP Server")

# Global client instance
weaviate_client = None

@click.command()
@click.option(
    "--connection-type",
    type=click.Choice(["local", "cloud"]),
    default="local",
    help="Connection type: local for Docker/self-hosted, cloud for WCS"
)
@click.option("--host", default="localhost", help="Host for local connection")
@click.option("--port", default=8080, type=int, help="HTTP port for local connection")
@click.option("--grpc-port", default=50051, type=int, help="gRPC port for local connection")
@click.option("--cluster-url", envvar="WEAVIATE_CLUSTER_URL", help="Weaviate Cloud Services cluster URL")
@click.option("--api-key", envvar="WEAVIATE_API_KEY", help="API key for authentication")
@click.option("--timeout-init", default=30, type=int, help="Initialization timeout in seconds")
@click.option("--timeout-query", default=60, type=int, help="Query timeout in seconds")
@click.option("--timeout-insert", default=120, type=int, help="Insert timeout in seconds")
@click.option("--cohere-api-key", envvar="COHERE_API_KEY", help="Cohere API key for embeddings")
@click.option("--openai-api-key", envvar="OPENAI_API_KEY", help="OpenAI API key for embeddings")
def cli(
    connection_type, host, port, grpc_port, cluster_url, api_key,
    timeout_init, timeout_query, timeout_insert, cohere_api_key, openai_api_key
):
    """Weaviate MCP Server - Interact with Weaviate via MCP"""

    # Build additional headers for third-party API keys
    additional_headers = {}
    if cohere_api_key:
        additional_headers["X-Cohere-Api-Key"] = cohere_api_key
    if openai_api_key:
        additional_headers["X-OpenAI-Api-Key"] = openai_api_key

    # Create configuration
    config = WeaviateConfig(
        connection_type=connection_type,
        host=host,
        port=port,
        grpc_port=grpc_port,
        cluster_url=cluster_url,
        api_key=api_key,
        timeout_init=timeout_init,
        timeout_query=timeout_query,
        timeout_insert=timeout_insert,
        additional_headers=additional_headers,
        cohere_api_key=cohere_api_key,
        openai_api_key=openai_api_key
    )

    # Validate configuration
    if connection_type == "cloud" and (not cluster_url or not api_key):
        click.echo("Error: --cluster-url and --api-key are required for cloud connections", err=True)
        return

    # Initialize client manager
    global weaviate_client
    weaviate_client = WeaviateClientManager(config)

    # Register tools with the server
    register_tools(mcp, weaviate_client)

    # Run the server
    mcp.run()

if __name__ == "__main__":
    cli()
```

### 7. Configuration Examples

#### Local Weaviate (Docker) Configuration

For Claude Desktop config (`claude_desktop_config.json`):
```json
{
  "mcpServers": {
    "mcp-weaviate": {
      "command": "uvx",
      "args": [
        "mcp-weaviate",
        "--connection-type", "local",
        "--host", "localhost",
        "--port", "8080",
        "--grpc-port", "50051"
      ]
    }
  }
}
```

#### Weaviate Cloud Services (WCS) Configuration

```json
{
  "mcpServers": {
    "mcp-weaviate": {
      "command": "uvx",
      "args": [
        "mcp-weaviate",
        "--connection-type", "cloud",
        "--cluster-url", "https://your-cluster.weaviate.network",
        "--api-key", "${WEAVIATE_API_KEY}"
      ],
      "env": {
        "WEAVIATE_API_KEY": "your-api-key-here",
        "COHERE_API_KEY": "your-cohere-key-here"
      }
    }
  }
}
```

#### Development Configuration

```json
{
  "mcpServers": {
    "mcp-weaviate": {
      "command": "uv",
      "args": [
        "--directory", "/path/to/mcp-weaviate",
        "run",
        "python", "src/main.py",
        "--connection-type", "local"
      ]
    }
  }
}
```

### 8. Smithery Configuration

`smithery.yaml`:
```yaml
# Smithery configuration for cross-platform deployment
startCommand:
  type: stdio
  configSchema:
    type: object
    properties:
      connectionType:
        type: string
        enum: ["local", "cloud"]
        default: "local"
        description: Connection type (local for Docker/self-hosted, cloud for WCS)
      host:
        type: string
        default: "localhost"
        description: Host for local connection
      port:
        type: number
        default: 8080
        description: HTTP port for local connection
      grpcPort:
        type: number
        default: 50051
        description: gRPC port for local connection
      clusterUrl:
        type: string
        description: Weaviate Cloud Services cluster URL
      weaviateApiKey:
        type: string
        default: ""
        description: API key for Weaviate authentication
      cohereApiKey:
        type: string
        default: ""
        description: Cohere API key for embeddings (optional)
      openaiApiKey:
        type: string
        default: ""
        description: OpenAI API key for embeddings (optional)
      timeoutInit:
        type: number
        default: 30
        description: Initialization timeout in seconds
      timeoutQuery:
        type: number
        default: 60
        description: Query timeout in seconds
      timeoutInsert:
        type: number
        default: 120
        description: Insert timeout in seconds

  commandFunction: |
    (config) => {
      const args = [
        'mcp-weaviate',
        '--connection-type', config.connectionType || 'local'
      ];

      if (config.connectionType === 'local') {
        args.push('--host', config.host || 'localhost');
        args.push('--port', String(config.port || 8080));
        args.push('--grpc-port', String(config.grpcPort || 50051));
      } else if (config.connectionType === 'cloud') {
        if (config.clusterUrl) {
          args.push('--cluster-url', config.clusterUrl);
        }
      }

      if (config.timeoutInit) {
        args.push('--timeout-init', String(config.timeoutInit));
      }
      if (config.timeoutQuery) {
        args.push('--timeout-query', String(config.timeoutQuery));
      }
      if (config.timeoutInsert) {
        args.push('--timeout-insert', String(config.timeoutInsert));
      }

      const env = {};
      if (config.weaviateApiKey) {
        env.WEAVIATE_API_KEY = config.weaviateApiKey;
      }
      if (config.cohereApiKey) {
        env.COHERE_API_KEY = config.cohereApiKey;
      }
      if (config.openaiApiKey) {
        env.OPENAI_API_KEY = config.openaiApiKey;
      }
      if (config.clusterUrl) {
        env.WEAVIATE_CLUSTER_URL = config.clusterUrl;
      }

      return {
        command: 'uvx',
        args: args,
        env: env
      };
    }

  exampleConfig:
    connectionType: "local"
    host: "localhost"
    port: 8080
    grpcPort: 50051
    weaviateApiKey: ""
    timeoutInit: 30
    timeoutQuery: 60
    timeoutInsert: 120
```

### 9. Error Handling Strategy

Implement comprehensive error handling for both local and cloud connections:
- Connection errors with retry logic
- Authentication failures with clear messages
- Query validation errors
- Timeout handling
- Rate limiting awareness
- Graceful degradation for missing features

### 10. Testing Strategy

#### Unit Tests
- Test each tool independently
- Mock Weaviate client responses
- Validate parameter schemas
- Test error conditions

#### Integration Tests
- Test against local Weaviate instance
- End-to-end tool execution
- Connection retry logic
- Authentication flows

#### Testing with FastMCP Client
```python
import asyncio
from fastmcp import Client

async def test_search():
    client = Client("src/main.py")
    async with client:
        result = await client.call_tool("search_objects", {
            "class_name": "Article",
            "query": "machine learning",
            "limit": 5
        })
        assert result["success"]
```

### 11. Documentation Structure

#### README.md sections:
1. **Overview** - What the MCP server does
2. **Installation** - UV and NPX installation methods
3. **Configuration** - Environment variables and CLI options
4. **Available Tools** - Complete tool reference
5. **Usage Examples** - Common scenarios
6. **Deployment** - Smithery deployment guide
7. **Development** - Contributing and testing

#### Tool Documentation Format:
Each tool should include:
- Purpose and use cases
- Parameter descriptions with types
- Return value structure
- Example requests and responses
- Common error conditions

### 12. Advanced Features (Future Enhancements)

- **Caching Layer**: Redis/in-memory caching for frequent queries
- **Streaming Responses**: For large result sets
- **Multi-tenancy Support**: Handle multiple Weaviate instances
- **Custom Vectorizers**: Support for different embedding models
- **Backup/Restore Tools**: Database management operations
- **Query Templates**: Predefined query patterns
- **Performance Monitoring**: Query metrics and logging

## Development Workflow

1. **Initial Setup**
   ```bash
   uv venv
   uv pip install -e ".[dev]"
   ```

2. **Development Server**
   ```bash
   uv run python src/main.py
   ```

3. **Testing**
   ```bash
   uv run pytest tests/
   ```

4. **Package for Distribution**
   ```bash
   uv build
   ```

## Deployment Options

### Local Development
- Direct Python execution
- UV run commands
- Docker container

### Production Deployment
- Smithery registry publication
- NPX installation support
- Cloud MCP hosting services
- Container orchestration (K8s)

## Success Metrics

- All core Weaviate operations accessible via MCP
- Sub-second response times for standard queries
- Comprehensive error messages
- 90%+ test coverage
- Compatible with Claude Desktop, Cursor, and other MCP clients
- Published to Smithery registry

## Timeline Estimate

- **Phase 1** (Core Implementation): 2-3 days
  - Basic project structure
  - Core tools implementation
  - Configuration management

- **Phase 2** (Testing & Polish): 1-2 days
  - Comprehensive testing
  - Error handling refinement
  - Documentation

- **Phase 3** (Deployment): 1 day
  - Smithery configuration
  - Package publication
  - Usage examples

Total estimated time: 4-6 days for production-ready MCP server
