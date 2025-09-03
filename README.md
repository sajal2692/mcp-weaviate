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

## Quick Start

The MCP server is designed to be used with MCP clients like Claude Desktop. It uses `uvx` for automatic installation and execution - no manual installation required.

Test the server directly:
```bash
uvx mcp-weaviate --help
```

## Requirements

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
      "command": "/path/to/uvx",
      "args": [
        "mcp-weaviate",
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
      "command": "/path/to/uvx",
      "args": [
        "mcp-weaviate",
        "--connection-type", "cloud",
        "--cluster-url", "https://your-cluster.weaviate.network",
        "--api-key", "YOUR_WEAVIATE_API_KEY",
        "--openai-api-key", "YOUR_OPENAI_API_KEY"
      ]
    }
  }
}
```


### Configuration Options

| Option | Description | Default | Environment Variable |
|--------|-------------|---------|---------------------|
| `--connection-type` | Connection type: "local" or "cloud" | *required* | - |
| `--host` | Host for local connection | *required for local* | - |
| `--port` | HTTP port for local connection | *required for local* | - |
| `--grpc-port` | gRPC port for local connection | *required for local* | - |
| `--cluster-url` | Weaviate Cloud Services URL | *required for cloud* | WEAVIATE_CLUSTER_URL |
| `--api-key` | API key for authentication | *required for cloud* | WEAVIATE_API_KEY |
| `--openai-api-key` | OpenAI API key for embeddings | - | OPENAI_API_KEY |
| `--cohere-api-key` | Cohere API key for embeddings | - | COHERE_API_KEY |
| `--timeout-init` | Initialization timeout (seconds) | 30 | - |
| `--timeout-query` | Query timeout (seconds) | 60 | - |
| `--timeout-insert` | Insert timeout (seconds) | 120 | - |

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

Example:
```bash
uv run python -m src.main \
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
