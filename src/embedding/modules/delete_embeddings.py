

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