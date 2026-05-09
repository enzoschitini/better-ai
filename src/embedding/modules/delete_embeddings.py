

from src.embedding.modules.config import GetConfig
from src.embedding.services.vector_db_connection import VectorDBConnection

class DeleteEmbeddings:
    def __init__(self, config_name=None):
        config = GetConfig()
        self.vector_db_settings = config.delete_embeddings().get(config_name if config_name else "vector_db_settings", {})
        self.pine_client = None
        self.pine_service = None
    
    def _get_vector_db(self):
        try:
            vector_db_connection = VectorDBConnection(vector_db_settings=self.vector_db_settings)
            self.pine_client, self.pine_service = vector_db_connection.get_pinecone_vector_db()

        except Exception as e:
            raise RuntimeError(f"Failed to load vector store database: {str(e)}")
    
    def delete(
        self,
        target_names: list[str],
        target_values: list[str],
        limit_targets: list[str] = None,
    ):
        if limit_targets and not any(target in limit_targets for target in target_names):
            raise ValueError(f"None of the target names {target_name} are in the allowed limit targets {limit_targets}.")
        
        self._get_vector_db()

        for target_name, target_value in zip(target_names, target_values):
            self.pine_service.delete_documents(
                target_feature=target_name,
                target_id=target_value,
                namespace=self.vector_db_settings.get("main_namespace")
            )

            if self.vector_db_settings.get("save_global", True):
                self.pine_service.delete_documents(
                    target_feature=target_name,
                    target_id=target_value,
                    namespace=self.vector_db_settings.get("global_namespace")
                )

if __name__ == "__main__":
    delete_embeddings = DeleteEmbeddings()
    delete_embeddings.delete(
        target_names=["knowledge_base_id"],
        target_values=["test_agent"]
    )


payload = {
    "vector_db_settings": {
        "index_name": "test-agent",
        "embedding_model": "text-embedding-3-small",
        "main_namespace": "test_agent",
        "global_namespace": "global",
        "save_global": True
    },
    "target_key": "knowledge_base_id",
    "target_value": "test_agent",
    "targets_to_limit": ["knowledge_base_id"]
}

# python -m src.embedding.modules.delete_embeddings