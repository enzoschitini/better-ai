```python
from src.embedding.modules.config import GetConfig
from src.embedding.services.vector_db_connection import VectorDBConnection
from src.tracing.tracing_core import ApplicationTracing

tracer = ApplicationTracing(
    flag="Delete Embeddings",
    file_name="delete_embeddings.py",
    log_file_name="delete_embeddings",
    show_info_logs=True
)

class DeleteEmbeddings:
    """
    This class provides functionality to delete embeddings from a vector database based on specified target keys and values.
    It manages connection settings to the vector database and supports deletion in multiple namespaces.

    Args: 
    :param vector_db_settings (dict): Settings for the vector database connection. Default is None, which applies default settings from configuration.

    Methods:
            delete(): Performs the deletion of embeddings in the configured namespaces based on the provided keys and values.
    """
    def __init__(self, vector_db_settings=None):
        self.config = GetConfig()
        default_settings = self.config.vector_db_settings()

        self.vector_db_settings = {
            **default_settings,
            **(vector_db_settings or {})
        }

        self.pine_client = None
        self.pine_service = None

        tracer.INFO(
            message="Initialized DeleteEmbeddings with vector_db_settings",
            metadata=self.vector_db_settings
        )

    def _get_vector_db(self):
        """
        Attempts to establish a connection to the vector database and initializes client and service properties.

        Raises:
            RuntimeError: If the vector store database connection fails.
        """
        try:
            vector_db_connection = VectorDBConnection(
                vector_db_settings=self.vector_db_settings
            )
            self.pine_client, self.pine_service = vector_db_connection.get_vector_db()

        except Exception as e:
            raise RuntimeError(f"Failed to load vector store database: {str(e)}")

    # -----------------------------
    # VALIDATION
    # -----------------------------
    def _validate_targets(self, target_keys, targets_to_limit):
        """
        Checks if any target keys are present in the allowed targets to limit the deletion scope.

        Args: 
        target_keys (list): List of target key names to validate.
        targets_to_limit (list or None): List of allowed target names to restrict deletion. If None, no restriction applies.

        Raises:
            ValueError: If none of the target keys are in the allowed limit targets.
        """
        if targets_to_limit and not any(
            target in targets_to_limit for target in target_keys
        ):
            raise ValueError(
                f"None of the target names {target_keys} are in the allowed limit targets {targets_to_limit}."
            )

    # -----------------------------
    # DELETION EXECUTION
    # -----------------------------
    def _delete_from_namespaces(self, target_name, target_value, main_ns, global_ns, save_global):
        """
        Deletes documents matching the target_name and target_value from the main namespace and optionally the global namespace.

        Args:
        target_name (str): Name of the feature to target for deletion.
        target_value (str): Value of the target feature used to identify documents to delete.
        main_ns (str): Main namespace in the vector database.
        global_ns (str): Global namespace to optionally delete from.
        save_global (bool): Flag indicating if deletion should also occur in the global namespace.

        Returns:
                list: Events detailing the deletion operation results for each namespace.
        """
        events = []

        tracer.INFO(
            message="Deleting from main namespace",
            metadata={
                "target_name": target_name,
                "target_value": target_value,
                "namespace": main_ns
            }
        )

        main_result = self.pine_service.delete_documents(
            target_feature=target_name,
            target_id=target_value,
            namespace=main_ns
        )

        events.append({
            "namespace": main_ns,
            "target_name": target_name,
            "target_value": target_value,
            "deleted_vectors": main_result.get("deleted_vectors", 0)
        })

        if save_global:
            tracer.INFO(
                message="Deleting from global namespace",
                metadata={
                    "target_name": target_name,
                    "target_value": target_value,
                    "namespace": global_ns
                }
            )

            global_result = self.pine_service.delete_documents(
                target_feature=target_name,
                target_id=target_value,
                namespace=global_ns
            )

            events.append({
                "namespace": global_ns,
                "target_name": target_name,
                "target_value": target_value,
                "deleted_vectors": global_result.get("deleted_vectors", 0)
            })

        return events

    # -----------------------------
    # AGGREGATION
    # -----------------------------
    def _aggregate_events(self, events):
        """
        Aggregates deletion events by namespace, totaling the deleted vectors and grouping items by namespace.

        Args:
        events (list): List of event dictionaries containing deletion details.

        Returns:
                list: Aggregated list of namespaces with their deletion summaries and items.
        """
        grouped = {}

        for item in events:
            ns = item["namespace"]

            if ns not in grouped:
                grouped[ns] = {
                    "namespace": ns,
                    "deleted_vectors": 0,
                    "items": []
                }

            grouped[ns]["deleted_vectors"] += item["deleted_vectors"]
            grouped[ns]["items"].append({
                "target_name": item["target_name"],
                "target_value": item["target_value"],
                "deleted_vectors": item["deleted_vectors"]
            })

        return list(grouped.values())

    # -----------------------------
    # PUBLIC METHOD
    # -----------------------------
    def delete(self, target_keys, target_values, targets_to_limit=None):
        """
        Executes the complete deletion process by validating targets, connecting to the vector DB,
        deleting from namespaces, aggregating results, and returning a summary.

        Args:
        target_keys (list): List of target feature names to delete by.
        target_values (list): List of target feature values associated with target_keys.
        targets_to_limit (list or None): Optional list of allowed targets to restrict deletion.

        Returns:
                dict: Summary of the deletion operation including total deleted vectors and breakdown by namespace.

        Raises:
                ValueError: If target keys are not within the allowed targets to limit.
                RuntimeError: If vector database connection or operations fail.
        """
        tracer.INFO(
            message="Starting delete operation",
            metadata={
                "target_keys": target_keys,
                "target_values": target_values
            }
        )

        self._validate_targets(target_keys, targets_to_limit)
        self._get_vector_db()

        main_ns = self.vector_db_settings.get("main_namespace")
        global_ns = self.vector_db_settings.get("global_namespace")
        save_global = self.vector_db_settings.get("save_global", True)

        all_events = []
        total_deleted = 0

        for target_name, target_value in zip(target_keys, target_values):
            events = self._delete_from_namespaces(
                target_name,
                target_value,
                main_ns,
                global_ns,
                save_global
            )

            all_events.extend(events)
            total_deleted += sum(e["deleted_vectors"] for e in events)

        deleted_by_namespace = self._aggregate_events(all_events)

        results = {
            "success": True,
            "summary": {
                "total_deleted_vectors": total_deleted,
                "namespaces_count": len(deleted_by_namespace)
            },
            "deleted_by_namespace": deleted_by_namespace
        }

        tracer.INFO(
            message="Delete operation completed",
            metadata=results
        )

        return results

if __name__ == "__main__":
    import json

    payload = {
        "vector_db_settings": {
            "index_name": "test-agent",
            "embedding_model": "text-embedding-3-small",
            "main_namespace": "test_agent",
            "global_namespace": "global",
        },
        "target_keys": ["knowledge_base_id"],
        "target_values": ["test_agent"],
        "targets_to_limit": ["knowledge_base_id"]
    }

    delete_embeddings = DeleteEmbeddings()
    result = delete_embeddings.delete(
        target_keys=payload["target_keys"],
        target_values=payload["target_values"],
        targets_to_limit=payload["targets_to_limit"]
    )

    print(json.dumps(result, indent=2))


# python -m src.embedding.modules.delete_embeddings
```