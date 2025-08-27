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
- Environment variable parsing
- CLI argument handling with Click
- Configuration validation with Pydantic
- Support for multiple authentication methods:
  - API Key authentication
  - OIDC authentication
  - Anonymous access

Configuration options:
```python
class WeaviateConfig:
    url: str                    # Weaviate instance URL
    api_key: Optional[str]      # API key for authentication
    timeout: int = 30           # Request timeout in seconds
    grpc_port: Optional[int]    # gRPC port for faster operations
    additional_headers: Dict    # Custom headers
    startup_period: int = 5     # Connection retry period
```

### 4. Weaviate Client Wrapper

`src/weaviate_client.py`:
```python
class WeaviateClient:
    """Wrapper for Weaviate operations with connection management"""
    
    def __init__(self, config: WeaviateConfig):
        # Initialize connection with retry logic
        # Setup authentication
        # Configure timeout and headers
        pass
    
    async def connect(self):
        """Establish connection to Weaviate"""
        pass
    
    async def disconnect(self):
        """Clean up connections"""
        pass
    
    # Core operations
    async def search(self, ...):
        """Perform vector/hybrid search"""
        pass
    
    async def get_schema(self):
        """Retrieve database schema"""
        pass
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
from src.config import WeaviateConfig, load_config
from src.weaviate_client import WeaviateClient
from src.tools import register_tools

# Initialize FastMCP server
mcp = FastMCP("Weaviate MCP Server")

# Global client instance
weaviate_client = None

@click.command()
@click.option("--url", envvar="WEAVIATE_URL", help="Weaviate instance URL")
@click.option("--api-key", envvar="WEAVIATE_API_KEY", help="API key for authentication")
@click.option("--timeout", default=30, help="Request timeout in seconds")
@click.option("--grpc-port", type=int, help="gRPC port for faster operations")
def cli(url, api_key, timeout, grpc_port):
    """Weaviate MCP Server - Interact with Weaviate via MCP"""
    
    # Load configuration
    config = load_config(url, api_key, timeout, grpc_port)
    
    # Initialize client
    global weaviate_client
    weaviate_client = WeaviateClient(config)
    
    # Register tools with the server
    register_tools(mcp, weaviate_client)
    
    # Run the server
    mcp.run()

if __name__ == "__main__":
    cli()
```

### 7. Smithery Configuration

`smithery.yaml`:
```yaml
# Smithery configuration for cross-platform deployment
startCommand:
  type: stdio
  configSchema:
    type: object
    required: ["weaviateUrl"]
    properties:
      weaviateUrl:
        type: string
        description: Weaviate instance URL (e.g., http://localhost:8080)
      weaviateApiKey:
        type: string
        default: ""
        description: API key for Weaviate authentication
      timeout:
        type: number
        default: 30
        description: Request timeout in seconds
      grpcPort:
        type: number
        description: gRPC port for faster operations (optional)
      searchLimit:
        type: number
        default: 10
        description: Default limit for search results
  
  commandFunction: |
    (config) => ({
      command: 'uv',
      args: ['run', 'python', 'src/main.py'],
      env: {
        WEAVIATE_URL: config.weaviateUrl,
        WEAVIATE_API_KEY: config.weaviateApiKey || '',
        WEAVIATE_TIMEOUT: String(config.timeout),
        WEAVIATE_GRPC_PORT: config.grpcPort ? String(config.grpcPort) : '',
        WEAVIATE_SEARCH_LIMIT: String(config.searchLimit)
      }
    })
  
  exampleConfig:
    weaviateUrl: "http://localhost:8080"
    weaviateApiKey: ""
    timeout: 30
    searchLimit: 10
```

### 8. Error Handling Strategy

Implement comprehensive error handling:
- Connection errors with retry logic
- Authentication failures with clear messages
- Query validation errors
- Timeout handling
- Rate limiting awareness
- Graceful degradation for missing features

### 9. Testing Strategy

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

### 10. Documentation Structure

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

### 11. Advanced Features (Future Enhancements)

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