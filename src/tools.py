import logging
from typing import Any

from src.config import WeaviateConfig
from src.weaviate_client import WeaviateClientManager


def register_tools(mcp: Any, config: WeaviateConfig) -> None:
    """Register all MCP tools with the FastMCP server."""

    logger = logging.getLogger(__name__)
    client_manager = WeaviateClientManager(config)

    @mcp.tool
    def get_config() -> dict[str, Any]:
        """Get the current Weaviate configuration (for testing)."""
        return {
            "connection_type": config.connection_type,
            "host": config.host,
            "port": config.port,
            "grpc_port": config.grpc_port,
            "cluster_url": config.cluster_url,
            "api_key": "***" if config.api_key else None,
            "timeout_init": config.timeout_init,
            "timeout_query": config.timeout_query,
            "timeout_insert": config.timeout_insert,
            "startup_period": config.startup_period,
            "cohere_api_key": "***" if config.cohere_api_key else None,
            "openai_api_key": "***" if config.openai_api_key else None,
            "additional_headers": dict.fromkeys(config.additional_headers.keys(), "***")
            if config.additional_headers
            else {},
        }

    @mcp.tool
    def check_connection() -> dict[str, Any]:
        """Check if the Weaviate connection is working."""
        try:
            is_ready = client_manager.is_ready()
            result: dict[str, Any] = {
                "connected": is_ready,
                "connection_type": config.connection_type,
            }
            if config.connection_type == "local":
                result["host"] = config.host
            else:
                result["cluster_url"] = config.cluster_url
            return result
        except Exception as e:
            logger.error(f"Error checking connection: {e}")
            return {
                "connected": False,
                "error": str(e),
                "connection_type": config.connection_type,
            }

    @mcp.tool
    def list_collections() -> dict[str, Any]:
        """List available Weaviate collections."""
        try:
            client = client_manager.get_client()
            collections = client.collections.list_all()
            return {"collections": list(collections), "total": len(collections)}
        except Exception as e:
            logger.error(f"Error listing collections: {e}")
            return {"error": str(e), "collections": [], "total": 0}

    @mcp.tool
    def get_schema(collection_name: str | None = None) -> dict[str, Any]:
        """Get schema information for Weaviate collections."""
        try:
            if collection_name:
                # Get schema for specific collection
                client = client_manager.get_client()
                collection = client.collections.get(collection_name)
                config = collection.config.get()

                properties = []
                if hasattr(config, "properties") and config.properties:
                    for prop in config.properties:
                        prop_info = {
                            "name": prop.name,
                            "data_type": prop.data_type,
                        }
                        if hasattr(prop, "description") and prop.description:
                            prop_info["description"] = prop.description
                        properties.append(prop_info)

                return {
                    "collection": collection_name,
                    "properties": properties,
                }
            else:
                # Get full schema
                return client_manager.get_schema()

        except Exception as e:
            logger.error(
                f"Error getting schema for {collection_name or 'all collections'}: {e}"
            )
            if collection_name:
                return {
                    "error": f"Collection {collection_name} not found or error: {str(e)}"
                }
            else:
                return {"error": str(e), "collections": []}

    @mcp.tool
    def search_vector(
        query: str, collection_name: str = "Article", limit: int = 5
    ) -> dict[str, Any]:
        """Search for objects in Weaviate using vector similarity."""
        try:
            client = client_manager.get_client()
            collection = client.collections.get(collection_name)

            # Perform vector search using the query text
            response = collection.query.near_text(
                query=query, limit=limit, return_metadata=["score"]
            )

            results = []
            for obj in response.objects:
                result: dict[str, Any] = {
                    "id": str(obj.uuid),
                    "collection": collection_name,
                    "properties": obj.properties,
                }

                # Add score if available
                if hasattr(obj.metadata, "score") and obj.metadata.score is not None:
                    result["score"] = float(obj.metadata.score)

                results.append(result)

            return {
                "results": results,
                "total": len(results),
                "query": query,
                "collection_name": collection_name,
            }

        except Exception as e:
            logger.error(f"Error searching collection {collection_name}: {e}")
            return {
                "error": str(e),
                "results": [],
                "total": 0,
                "query": query,
                "collection_name": collection_name,
            }

    @mcp.tool
    def get_collection_objects(
        collection_name: str, limit: int = 10, offset: int = 0
    ) -> dict[str, Any]:
        """Get objects from a specific collection."""
        try:
            client = client_manager.get_client()
            collection = client.collections.get(collection_name)

            response = collection.query.fetch_objects(limit=limit, offset=offset)

            results = []
            for obj in response.objects:
                results.append(
                    {
                        "id": str(obj.uuid),
                        "collection": collection_name,
                        "properties": obj.properties,
                    }
                )

            return {
                "results": results,
                "total": len(results),
                "collection_name": collection_name,
                "limit": limit,
                "offset": offset,
            }

        except Exception as e:
            logger.error(
                f"Error getting objects from collection {collection_name}: {e}"
            )
            return {
                "error": str(e),
                "results": [],
                "total": 0,
                "collection_name": collection_name,
            }

    @mcp.tool
    def greet(name: str) -> str:
        """Greet someone by name."""
        return f"Hello, {name}! Welcome to the Weaviate MCP Server."
