from typing import List, Dict, Any

class RetrievalManager:
    """
    Classe responsável por gerenciar documentos recuperados (retrieval),
    permitindo filtragem por score, geração de contexto compacto e extração de metadados de arquivos.

    :param docs: Lista de documentos contendo pelo menos 'text', 'score' e opcionalmente 'metadata'
    :param score_min: Valor mínimo de score para filtragem
    :param filter_by_score: Define se os documentos devem ser filtrados automaticamente na inicialização
    """
    def __init__(self, docs: List[Dict[str, Any]], score_min: float = 0.0, filter_by_score: bool = False):
        self.docs = docs
        self.score_min = score_min
        self.filter_by_score = filter_by_score

        if self.filter_by_score:
            self.docs = self.get_by_score(self.docs, self.score_min)

    def get_by_score(self, docs: List[Dict[str, Any]] = None, score_min: float = 0.0) -> List[Dict[str, Any]]:
        """
        Filtra itens de uma lista de documentos com base no score mínimo.

        :param docs: Lista de dicionários com a chave 'score'
        :param score_min: Valor mínimo de score (>=)
        :return: Lista filtrada
        """
        try:
            docs = docs or self.docs
            return [item for item in docs if item.get("score", 0) >= score_min]
        
        except Exception as e:
            raise RuntimeError("Failed to filter documents by score:", str(e))

    def generate_context(self, docs: List[Dict[str, Any]] = None) -> str:
        """
        Converte documentos para um formato compacto estilo toon.

        Cada linha segue o padrão:
        score|content

        :param docs: Lista de documentos (com 'text' e 'score')
        :return: String compacta para uso em LLM
        """
        try:
            docs = docs or self.docs

            return "\n".join(
                f"Score: {round(doc.get('score', 0), 2)} | Content: {doc.get('text', '').replace('\n', ' ')}"
                for doc in docs
            )

        except Exception as e:
            raise RuntimeError("Failed to generate context string:", str(e))

    def get_files(self, docs: List[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Extrai informações de arquivos a partir dos metadados dos documentos.

        Cada documento pode conter um campo 'metadata' com informações do arquivo original.
        Este método organiza esses dados em uma estrutura padronizada.

        :param docs: Lista de documentos contendo 'metadata'
        :return: Lista de dicionários com:
            - id: Identificador do arquivo
            - name: Nome do arquivo
            - ext: Extensão do arquivo
            - score: Score associado ao documento
        """
        try:
            docs = docs or self.docs
            files_map = {}

            for doc in docs:
                metadata = doc.get("metadata", {})
                file_id = metadata.get("file_id")

                if not file_id:
                    continue

                current_score = doc.get("score", 0)

                if file_id not in files_map or current_score > files_map[file_id]["score"]:
                    files_map[file_id] = {
                        "id": file_id,
                        "name": metadata.get("file_name"),
                        "ext": metadata.get("file_extension"),
                        "score": current_score,
                    }

            return list(files_map.values())

        except Exception as e:
            raise RuntimeError("Failed to extract file metadata:", str(e))


if __name__ == "__main__":
    import json
    documents = [
        {
            "id": "79258322-c06b-4e50-9a69-c8caa1136b3f",
            "text": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "metadata": {
                "Client": "1234",
                "client_id": "0011",
                "collection_id": "collection_01",
                "collection_name": "BetterAI",
                "created_at": "2026-03-25 18:58:43",
                "file_extension": "pdf",
                "file_id": "cucinare",
                "file_name": "LESSICO per CUCINARE.pdf",
                "user_id": "11"
            },
            "score": 0.382682741
        },

        {
            "id": "f75b0f7c-36ab-48d4-8da0-ec21b9ce688a",
            "text": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "metadata": {
                "Client": "1234",
                "client_id": "0011",
                "collection_id": "collection_01",
                "collection_name": "BetterAI",
                "created_at": "2026-03-25 18:58:43",
                "file_extension": "pdf",
                "file_id": "tenerezza",
                "file_name": "TENEREZZA.pdf",
                "user_id": "11"
            },
            "score": 0.359430343
        },

        {
            "id": "f75b0f7c-36ab-48d4-8da0-ec21b9ce688a",
            "text": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
            "metadata": {
                "Client": "1234",
                "client_id": "0011",
                "collection_id": "collection_01",
                "collection_name": "BetterAI",
                "created_at": "2026-03-25 18:58:43",
                "file_extension": "pdf",
                "file_id": "tenerezza",
                "file_name": "TENEREZZA.pdf",
                "user_id": "11"
            },
            "score": 0.329430343
        },
    ]

    meneger = RetrievalManager(
        docs=documents,
        score_min=0.36,
        #filter_by_score=True
    )

    print(json.dumps(meneger.get_files(), indent=2))

# python -m src.vector_store.pinecone.utils.retrieval_manager