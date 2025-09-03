# Weaviate MCP Server

A Model Context Protocol (MCP) server that provides seamless integration with Weaviate vector databases. This server focuses on powerful search capabilities including semantic, keyword, and hybrid search, with plans to expand functionality in future releases.

## Features

The Weaviate MCP Server currently provides 11 essential tools for interacting with your Weaviate instance:

### Connection & Configuration
- **`get_config`** - View current Weaviate configuration (with sensitive values masked)
- **`check_connection`** - Test connection to your Weaviate instance

### Schema & Collection Management
- **`list_collections`** - List all available collections in your database
- **`get_schema`** - Get detailed schema information for specific collections or all collections
- **`get_collection_objects`** - Retrieve objects from collections with pagination support

### Search Capabilities (Primary Focus)
- **`search`** - Simplified search interface using hybrid search by default
- **`semantic_search`** - Vector similarity search using embeddings for semantic matching
- **`keyword_search`** - BM25-based keyword search for exact term matching
- **`hybrid_search`** - Combined semantic and keyword search with configurable weighting

### Multi-Tenancy Support
- **`is_multi_tenancy_enabled`** - Check if a collection supports multi-tenancy
- **`get_tenant_list`** - List all tenants for a multi-tenant collection

## Installation

### Using pip
```bash
pip install mcp-weaviate
```

### Using uv (recommended)
```bash
uv add mcp-weaviate
```

### From source
```bash
git clone https://github.com/yourusername/mcp-weaviate.git
cd mcp-weaviate
uv sync
```

## Requirements

- Python 3.12 or higher
- Weaviate instance (local or cloud)
- API keys for embeddings:
  - OpenAI API key (for OpenAI embeddings)
  - Cohere API key (optional, for Cohere embeddings)

## Configuration

### MCP Settings Configuration

Add the Weaviate MCP server to your MCP settings file (typically `claude_desktop_config.json` or similar):

#### Local Weaviate Instance

```json
{
  "mcpServers": {
    "mcp-weaviate": {
      "command": "/path/to/uv",
      "args": [
        "--directory",
        "/path/to/mcp-weaviate",
        "run",
        "python",
        "run_mcp_weaviate.py",
        "--connection-type", "local",
        "--host", "localhost",
        "--port", "8080",
        "--grpc-port", "50051",
        "--openai-api-key", "YOUR_OPENAI_API_KEY"
      ]
    }
  }
}
```

#### Weaviate Cloud Services

```json
{
  "mcpServers": {
    "mcp-weaviate": {
      "command": "/path/to/uv",
      "args": [
        "--directory",
        "/path/to/mcp-weaviate",
        "run",
        "python",
        "run_mcp_weaviate.py",
        "--connection-type", "cloud",
        "--cluster-url", "https://your-cluster.weaviate.network",
        "--api-key", "YOUR_WEAVIATE_API_KEY",
        "--openai-api-key", "YOUR_OPENAI_API_KEY"
      ]
    }
  }
}
```

#### Using Environment Variables (Recommended)

For better security, use environment variables for sensitive values:

```json
{
  "mcpServers": {
    "mcp-weaviate": {
      "command": "/path/to/uv",
      "args": [
        "--directory",
        "/path/to/mcp-weaviate",
        "run",
        "python",
        "run_mcp_weaviate.py",
        "--connection-type", "cloud"
      ],
      "env": {
        "WEAVIATE_CLUSTER_URL": "https://your-cluster.weaviate.network",
        "WEAVIATE_API_KEY": "YOUR_WEAVIATE_API_KEY",
        "OPENAI_API_KEY": "YOUR_OPENAI_API_KEY",
        "COHERE_API_KEY": "YOUR_COHERE_API_KEY"
      }
    }
  }
}
```

### Configuration Options

| Option | Description | Default | Environment Variable |
|--------|-------------|---------|---------------------|
| `--connection-type` | Connection type: "local" or "cloud" | local | - |
| `--host` | Host for local connection | localhost | - |
| `--port` | HTTP port for local connection | 8080 | - |
| `--grpc-port` | gRPC port for local connection | 50051 | - |
| `--cluster-url` | Weaviate Cloud Services URL | - | WEAVIATE_CLUSTER_URL |
| `--api-key` | API key for authentication | - | WEAVIATE_API_KEY |
| `--openai-api-key` | OpenAI API key for embeddings | - | OPENAI_API_KEY |
| `--cohere-api-key` | Cohere API key for embeddings | - | COHERE_API_KEY |
| `--timeout-init` | Initialization timeout (seconds) | 30 | - |
| `--timeout-query` | Query timeout (seconds) | 60 | - |
| `--timeout-insert` | Insert timeout (seconds) | 120 | - |

## Getting Started

### 1. Set up your Weaviate instance

For local development using Docker:
```bash
docker run -d \
  --name weaviate \
  -p 8080:8080 \
  -p 50051:50051 \
  --env AUTHENTICATION_ANONYMOUS_ACCESS_ENABLED='true' \
  --env PERSISTENCE_DATA_PATH='/var/lib/weaviate' \
  --env QUERY_DEFAULTS_LIMIT=25 \
  --env DEFAULT_VECTORIZER_MODULE='text2vec-openai' \
  --env ENABLE_MODULES='text2vec-openai' \
  --env CLUSTER_HOSTNAME='node1' \
  cr.weaviate.io/semitechnologies/weaviate:latest
```

### 2. Configure the MCP server

Add the configuration to your MCP settings as shown above.

### 3. Test the connection

Once configured, you can test the connection using the MCP client:

```python
# Check connection status
result = await mcp.call_tool("check_connection")
print(result)  # {"connected": true, "connection_type": "local", "host": "localhost"}

# List available collections
collections = await mcp.call_tool("list_collections")
print(collections)  # {"collections": ["Article", "Product"], "total": 2}
```

## Usage Examples

### Basic Search

```python
# Simple search (uses hybrid search by default)
results = await mcp.call_tool("search", {
    "query": "machine learning applications",
    "collection_name": "Article",
    "limit": 5
})
```

### Semantic Search

```python
# Find semantically similar content
results = await mcp.call_tool("semantic_search", {
    "query": "artificial intelligence in healthcare",
    "collection_name": "Article",
    "limit": 10
})
```

### Keyword Search

```python
# Exact keyword matching with BM25
results = await mcp.call_tool("keyword_search", {
    "query": "Python programming",
    "collection_name": "Tutorial",
    "limit": 5
})
```

### Hybrid Search with Custom Weighting

```python
# Balance between semantic and keyword search
results = await mcp.call_tool("hybrid_search", {
    "query": "climate change effects",
    "collection_name": "Research",
    "alpha": 0.7,  # 70% semantic, 30% keyword
    "limit": 10
})
```

### Working with Multi-Tenant Collections

```python
# Check if collection supports multi-tenancy
status = await mcp.call_tool("is_multi_tenancy_enabled", {
    "collection_name": "UserDocuments"
})

# Get list of tenants
tenants = await mcp.call_tool("get_tenant_list", {
    "collection_name": "UserDocuments"
})

# Search within a specific tenant
results = await mcp.call_tool("search", {
    "query": "project proposals",
    "collection_name": "UserDocuments",
    "tenant_id": "tenant-123",
    "limit": 5
})
```

### Schema Inspection

```python
# Get schema for a specific collection
schema = await mcp.call_tool("get_schema", {
    "collection_name": "Product"
})

# Get complete database schema
full_schema = await mcp.call_tool("get_schema")
```

## Tool Reference

### Search Tools

#### `search`
Simplified search interface using hybrid search with balanced defaults (alpha=0.3).

#### `semantic_search`
Vector similarity search using embeddings. Best for finding conceptually similar content.

#### `keyword_search`
BM25 keyword search for exact term matching. Best for finding specific terms or phrases.

#### `hybrid_search`
Combines semantic and keyword search using Reciprocal Rank Fusion (RRF).
- `alpha` parameter controls the balance:
  - 1.0 = 100% semantic search
  - 0.0 = 100% keyword search
  - 0.5 = equal weight
  - 0.3 = default (30% semantic, 70% keyword)

### Collection Management

#### `get_collection_objects`
Retrieve objects from a collection with pagination support:
- `limit`: Maximum number of objects to return
- `offset`: Number of objects to skip (for pagination)

### Multi-Tenancy

All search and retrieval tools support an optional `tenant_id` parameter for multi-tenant collections.

## Roadmap

The Weaviate MCP Server currently focuses on comprehensive search capabilities. Future releases will include:

- **Data Management**
  - Object creation and updates
  - Batch imports
  - Delete operations

- **Advanced Query Features**
  - Filtering and where clauses
  - Aggregations
  - GraphQL query support

- **Collection Management**
  - Create/modify collections
  - Index management
  - Backup and restore operations

- **Enhanced Search**
  - Generative search (RAG)
  - Question answering
  - Custom ranking functions

## Development

### Setting up for development

```bash
# Clone the repository
git clone https://github.com/yourusername/mcp-weaviate.git
cd mcp-weaviate

# Install dependencies with uv
uv sync

# Install development dependencies
uv sync --dev

# Run tests
uv run pytest

# Run linting
uv run ruff check .

# Run type checking
uv run mypy .
```

### Running locally

```bash
# Run the MCP server directly
uv run python run_mcp_weaviate.py --connection-type local

# Or with all options
uv run python run_mcp_weaviate.py \
  --connection-type cloud \
  --cluster-url https://your-cluster.weaviate.network \
  --api-key YOUR_API_KEY \
  --openai-api-key YOUR_OPENAI_KEY
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

MIT License - see LICENSE file for details.

## Support

For issues, questions, or suggestions, please open an issue on the GitHub repository.
