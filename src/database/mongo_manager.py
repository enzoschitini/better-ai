import os

from datetime import datetime
from pymongo import MongoClient

from dotenv import load_dotenv
from src.chat.utils.logging_utils import setup_logging

load_dotenv()
setup_logging()

class MongoDBManager:
    """
    Gerenciador de conexão e operações básicas com MongoDB.

    Responsável por gerenciar a conexão com o banco e executar operações
    de inserção, busca, atualização e remoção de documentos.

    :param self: Instância do gerenciador de MongoDB.
    :type self: MongoDBManager

    :note: A conexão é reutilizada enquanto a instância existir.
           Em caso de erro, a conexão é fechada automaticamente.
    """
    def __init__(self, mongo_uri: str = None):
        self.mongo_uri = mongo_uri or os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.client = None

    def connect(self):
        """
        Cria e retorna uma conexão ativa com o MongoDB.

        :param self: Instância do gerenciador de MongoDB.
        :type self: MongoDBManager

        :return: Cliente MongoDB conectado.
        :rtype: MongoClient

        :note: A conexão é criada apenas na primeira chamada e reutilizada
            nas chamadas seguintes.
        """
        if not self.client:
            self.client = MongoClient(self.mongo_uri)
        return self.client

    def close_connection(self):
        """
        Encerra a conexão ativa com o MongoDB.

        :param self: Instância do gerenciador de MongoDB.
        :type self: MongoDBManager

        :note: Deve ser utilizado ao finalizar a aplicação ou em cenários de erro.
        """
        if self.client:
            self.client.close()
            self.client = None

    def save_payload(self, database_name: str, collection_name: str, payload: dict):
        """
        Insere um documento em uma collection do MongoDB.

        :param self: Instância do gerenciador de MongoDB.
        :type self: MongoDBManager
        :param database_name: Nome do banco de dados.
        :type database_name: str
        :param collection_name: Nome da collection.
        :type collection_name: str
        :param payload: Documento a ser inserido.
        :type payload: dict

        :return: Status da operação e ID do documento inserido.
        :rtype: Dict[str, Any]

        :note: O campo `_created_at` é adicionado automaticamente ao documento.
        """
        try:
            client = self.connect()
            db = client[database_name]
            collection = db[collection_name]

            payload["_created_at"] = datetime.utcnow()
            result = collection.insert_one(payload)

            return {"status": "success", "inserted_id": str(result.inserted_id)}

        except Exception as e:
            self.close_connection()
            raise RuntimeError(f"Error saving to MongoDB: {e}")

    def fetch_documents(
        self,
        database_name: str,
        collection_name: str,
        filter: dict = None,
        limit: int = 0
    ):
        """
        Busca documentos em uma collection do MongoDB com base em filtros opcionais.

        :param self: Instância do gerenciador de MongoDB.
        :type self: MongoDBManager
        :param database_name: Nome do banco de dados.
        :type database_name: str
        :param collection_name: Nome da collection.
        :type collection_name: str
        :param filter: Filtro de busca no formato do MongoDB.
        :type filter: dict, opcional
        :param limit: Quantidade máxima de documentos retornados. Se 0, retorna todos.
        :type limit: int, opcional

        :return: Lista de documentos encontrados.
        :rtype: List[Dict[str, Any]]

        :note: O campo `_id` é convertido para string automaticamente.
        """
        filter = filter or {}

        try:
            client = self.connect()
            db = client[database_name]
            collection = db[collection_name]

            cursor = collection.find(filter).limit(limit) if limit > 0 else collection.find(filter)
            documents = []

            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                documents.append(doc)

            return documents

        except Exception as e:
            self.close_connection()
            raise RuntimeError(f"Error fetching documents: {e}")

    def update_documents(
        self,
        database_name: str,
        collection_name: str,
        filter: dict,
        new_values: dict,
        multi: bool = False
    ):
        """
        Atualiza um ou múltiplos documentos em uma collection do MongoDB.

        :param self: Instância do gerenciador de MongoDB.
        :type self: MongoDBManager
        :param database_name: Nome do banco de dados.
        :type database_name: str
        :param collection_name: Nome da collection.
        :type collection_name: str
        :param filter: Filtro para localizar os documentos.
        :type filter: dict
        :param new_values: Novos valores a serem aplicados.
        :type new_values: dict
        :param multi: Define se a atualização será em múltiplos documentos.
        :type multi: bool

        :return: Status da operação e métricas de atualização.
        :rtype: Dict[str, Any]

        :note: O campo `_id` é ignorado caso seja enviado em `new_values`.
            O campo `updated_at` é adicionado automaticamente.
        """
        try:
            client = self.connect()
            db = client[database_name]
            collection = db[collection_name]

            new_values = new_values.copy()
            new_values.pop("_id", None)

            new_values["updated_at"] = datetime.utcnow()
            update_op = {"$set": new_values}

            if multi:
                result = collection.update_many(filter, update_op)
                message = f"{result.modified_count} document(s) updated"
            else:
                result = collection.update_one(filter, update_op)
                message = "1 document updated" if result.modified_count > 0 else "No documents updated"

            return {
                "status": "success",
                "matched_count": result.matched_count,
                "modified_count": result.modified_count,
                "message": message
            }

        except Exception as e:
            self.close_connection()
            raise RuntimeError(f"Error updating documents: {e}")

    def delete_documents(
        self,
        database_name: str,
        collection_name: str,
        filter: dict,
        multi: bool = False
    ):
        """
        Remove um ou múltiplos documentos de uma collection do MongoDB.

        :param self: Instância do gerenciador de MongoDB.
        :type self: MongoDBManager
        :param database_name: Nome do banco de dados.
        :type database_name: str
        :param collection_name: Nome da collection.
        :type collection_name: str
        :param filter: Filtro para localizar os documentos.
        :type filter: dict
        :param multi: Define se a remoção será em múltiplos documentos.
        :type multi: bool

        :return: Status da operação e quantidade de documentos removidos.
        :rtype: Dict[str, Any]

        :note: Operação irreversível. Evite utilizar sem filtros em ambientes de produção.
        """
        try:
            client = self.connect()
            db = client[database_name]
            collection = db[collection_name]

            if multi:
                result = collection.delete_many(filter)
                message = f"{result.deleted_count} document(s) deleted"
            else:
                result = collection.delete_one(filter)
                message = "1 document deleted" if result.deleted_count > 0 else "No documents deleted"

            return {
                "status": "success",
                "deleted_count": result.deleted_count,
                "message": message
            }

        except Exception as e:
            self.close_connection()
            raise RuntimeError(f"Error deleting documents: {e}")
