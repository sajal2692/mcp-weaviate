"""Weaviate client setup and management."""

import logging
from typing import Any

import weaviate
from weaviate.classes.init import Timeout

from src.config import WeaviateConfig

logger = logging.getLogger(__name__)


class WeaviateClientManager:
    """Manages Weaviate client connections for both local and cloud deployments."""

    def __init__(self, config: WeaviateConfig) -> None:
        """Initialize the client manager with configuration."""
        self.config = config
        self._client: weaviate.WeaviateClient | None = None

    def get_client(self) -> weaviate.WeaviateClient:
        """Get or create a Weaviate client instance."""
        if self._client is None:
            self._client = self._create_client()
        return self._client

    def _create_client(self) -> weaviate.WeaviateClient:
        """Create a new Weaviate client based on configuration."""
        timeout = Timeout(
            init=self.config.timeout_init,
            query=self.config.timeout_query,
            insert=self.config.timeout_insert,
        )

        if self.config.connection_type == "local":
            return self._create_local_client(timeout)
        else:
            return self._create_cloud_client(timeout)

    def _create_local_client(self, timeout: Timeout) -> weaviate.WeaviateClient:
        """Create a client for local Weaviate instance."""
        host = self.config.host or "localhost"
        port = self.config.port or 8080
        grpc_port = self.config.grpc_port or 50051

        url = f"http://{host}:{port}"
        grpc_url = f"{host}:{grpc_port}"

        logger.info(f"Connecting to local Weaviate at {url} (gRPC: {grpc_url})")

        return weaviate.connect_to_local(
            host=host,
            port=port,
            grpc_port=grpc_port,
            headers=self.config.additional_headers,
        )

    def _create_cloud_client(self, timeout: Timeout) -> weaviate.WeaviateClient:
        """Create a client for Weaviate Cloud Services."""
        if not self.config.cluster_url or not self.config.api_key:
            raise ValueError(
                "cluster_url and api_key are required for cloud connections"
            )

        logger.info(f"Connecting to Weaviate Cloud at {self.config.cluster_url}")

        return weaviate.connect_to_weaviate_cloud(
            cluster_url=self.config.cluster_url,
            auth_credentials=self.config.api_key,
            headers=self.config.additional_headers,
        )

    def close(self) -> None:
        """Close the client connection."""
        if self._client is not None:
            self._client.close()
            self._client = None

    def is_ready(self) -> bool:
        """Check if the Weaviate instance is ready."""
        try:
            client = self.get_client()
            return bool(client.is_ready())
        except Exception as e:
            logger.error(f"Error checking readiness: {e}")
            return False

    def get_collection(self, collection_name: str) -> Any:
        """Get collection object without tenant context."""
        client = self.get_client()
        return client.collections.get(collection_name)

    def get_collection_with_tenant(self, collection_name: str, tenant_id: str) -> Any:
        """Get collection object with tenant context."""
        client = self.get_client()
        base_collection = client.collections.get(collection_name)
        return base_collection.with_tenant(tenant_id)

    def is_multi_tenancy_enabled(self, collection_name: str) -> bool:
        """Check if collection has multi-tenancy enabled."""
        try:
            client = self.get_client()
            collection = client.collections.get(collection_name)
            config = collection.config.get()

            if hasattr(config, "multi_tenancy_config"):
                return bool(config.multi_tenancy_config.enabled)
            return False
        except Exception as e:
            logger.error(
                f"Error checking multi-tenancy status for {collection_name}: {e}"
            )
            return False

    def get_tenant_list(self, collection_name: str) -> list[str]:
        """Get list of tenant names for a collection."""
        try:
            if not self.is_multi_tenancy_enabled(collection_name):
                return []

            client = self.get_client()
            collection = client.collections.get(collection_name)
            tenants = collection.tenants.get()

            # tenants.get() returns a dict where keys are tenant names
            if isinstance(tenants, dict):
                return list(tenants.keys())
            else:
                # Fallback for other formats
                return [t.name if hasattr(t, "name") else str(t) for t in tenants]
        except Exception as e:
            logger.error(f"Error getting tenant list for {collection_name}: {e}")
            return []

    def get_schema(self) -> dict[str, Any]:
        """Get the current schema from Weaviate."""
        try:
            client = self.get_client()
            collections = client.collections.list_all()

            schema: dict[str, Any] = {"collections": []}

            for collection in collections:
                collection_info: dict[str, Any] = {"name": collection, "properties": []}

                try:
                    # Get collection configuration
                    coll = client.collections.get(collection)
                    config = coll.config.get()

                    # Extract properties from config
                    if hasattr(config, "properties") and config.properties:
                        for prop in config.properties:
                            property_info = {
                                "name": prop.name,
                                "data_type": prop.data_type,
                            }
                            if hasattr(prop, "description") and prop.description:
                                property_info["description"] = prop.description
                            collection_info["properties"].append(property_info)

                    schema["collections"].append(collection_info)

                except Exception as e:
                    logger.warning(
                        f"Error getting config for collection {collection}: {e}"
                    )
                    # Add collection with basic info even if we can't get details
                    schema["collections"].append(
                        {"name": collection, "properties": [], "error": str(e)}
                    )

            return schema

        except Exception as e:
            logger.error(f"Error getting schema: {e}")
            return {"error": str(e), "collections": []}

    def __enter__(self) -> "WeaviateClientManager":
        """Context manager entry."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit."""
        self.close()
