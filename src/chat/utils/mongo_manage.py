from pymongo import MongoClient
from datetime import datetime
import os
from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

class MongoDBManager:
    """
    Classe para gerenciar operações com MongoDB.
    Inclui listagem, inserção, busca, atualização e deleção de documentos.
    """

    def __init__(self, mongo_uri: str = None):
        """
        Inicializa o gerenciador de conexão com o MongoDB.
        """
        self.mongo_uri = mongo_uri or os.getenv("MONGO_URI", "mongodb://localhost:27017")
        self.client = None

    # =============================
    # CONEXÃO
    # =============================
    def conectar(self):
        """Estabelece conexão com o MongoDB."""
        if not self.client:
            self.client = MongoClient(self.mongo_uri)
        return self.client

    def fechar_conexao(self):
        """Fecha a conexão com o MongoDB."""
        if self.client:
            self.client.close()
            self.client = None

    # =============================
    # LISTAGEM
    # =============================
    def listar_databases_e_colecoes(self):
        """Lista bancos, coleções e quantidades de documentos."""
        try:
            client = self.conectar()
            databases = client.list_database_names()
            resultado = {}

            #print("📂 Listando bancos, coleções e quantidades:\n")

            for db_name in databases:
                db = client[db_name]
                try:
                    colecoes = db.list_collection_names()
                except Exception as e:
                    #print(f"⚠️ MongoMenage  Não foi possível listar coleções de '{db_name}': {e}")
                    resultado[db_name] = {"_erro": "sem permissão para listar coleções"}
                    continue

                resultado[db_name] = {}
                #print(f"🗄️  Banco: {db_name}")

                if colecoes:
                    for col in colecoes:
                        try:
                            count = db[col].estimated_document_count()
                            resultado[db_name][col] = count
                            #print(f"   └── 📁 {col} ({count} documento{'s' if count != 1 else ''})")
                        except Exception:
                            resultado[db_name][col] = "acesso negado"
                            #print(f"   └── 📁 {col} (acesso negado)")
                else:
                    #print("   └── (sem coleções)")
                    pass
                
            return resultado

        except Exception as e:
            #print(f"❌ Erro ao listar bancos e coleções: {e}")
            return {}
        finally:
            self.fechar_conexao()

    # =============================
    # CREATE
    # =============================
    def salvar_payload(self, database_name: str, collection_name: str, payload: dict):
        """Insere um documento em uma coleção."""
        try:
            client = self.conectar()
            db = client[database_name]
            collection = db[collection_name]
            payload["_created_at"] = datetime.utcnow()
            result = collection.insert_one(payload)
            ##print(f"✅ Documento inserido em {database_name}.{collection_name} com ID: {result.inserted_id}")
            return {"status": "success", "inserted_id": str(result.inserted_id)}
        except Exception as e:
            #print(f"❌ Erro ao salvar no MongoDB: {e}")
            return {"status": "error", "message": str(e)}
        finally:
            self.fechar_conexao()

    # =============================
    # READ
    # =============================
    def buscar_documentos(self, database_name: str, collection_name: str, filtro: dict = None, limite: int = 0):
        """Busca documentos em uma coleção."""
        filtro = filtro or {}
        try:
            client = self.conectar()
            db = client[database_name]
            collection = db[collection_name]

            cursor = collection.find(filtro).limit(limite) if limite > 0 else collection.find(filtro)
            documentos = []

            for doc in cursor:
                doc["_id"] = str(doc["_id"])
                documentos.append(doc)

            return documentos

        except Exception as e:
            return f"❌ Erro ao buscar documentos: {e}"
        finally:
            self.fechar_conexao()

    # =============================
    # UPDATE
    # =============================
    def atualizar_documentos(self, database_name: str, collection_name: str, filtro: dict, novos_valores: dict, multi: bool = False):
        """Atualiza um ou mais documentos em uma coleção, mantendo o _id."""
        try:
            client = self.conectar()
            db = client[database_name]
            collection = db[collection_name]

            # Remove _id para não tentar atualizar campo imutável
            novos_valores = novos_valores.copy()  # não altera o original
            if '_id' in novos_valores:
                novos_valores.pop('_id')

            # Adiciona timestamp de atualização
            novos_valores["updated_at"] = datetime.utcnow()

            update_op = {"$set": novos_valores}

            if multi:
                result = collection.update_many(filtro, update_op)
                msg = f"✅ {result.modified_count} documento(s) atualizados"
            else:
                result = collection.update_one(filtro, update_op)
                msg = f"✅ 1 documento atualizado" if result.modified_count > 0 else "⚠️ Nenhum documento atualizado"

            ##print(msg)
            return {"status": "success", "matched_count": result.matched_count, "modified_count": result.modified_count}

        except Exception as e:
            #print(f"❌ Erro ao atualizar documentos: {e}")
            return {"status": "error", "message": str(e)}

        finally:
            self.fechar_conexao()

    # =============================
    # DELETE
    # =============================
    def deletar_documentos(self, database_name: str, collection_name: str, filtro: dict, multi: bool = False):
        """Deleta um ou mais documentos."""
        try:
            client = self.conectar()
            db = client[database_name]
            collection = db[collection_name]
            if multi:
                result = collection.delete_many(filtro)
                msg = f"✅ {result.deleted_count} documento(s) deletados"
            else:
                result = collection.delete_one(filtro)
                msg = "✅ 1 documento deletado" if result.deleted_count > 0 else "⚠️ Nenhum documento deletado"
            #print(msg)
            return {"status": "success", "deleted_count": result.deleted_count}
        except Exception as e:
            #print(f"❌ Erro ao deletar documentos: {e}")
            return {"status": "error", "message": str(e)}
        finally:
            self.fechar_conexao()

    def deletar_colecao_ou_database(self, database_name: str, collection_name: str = None):
        """Deleta uma coleção específica ou o banco de dados inteiro."""
        try:
            client = self.conectar()
            db = client[database_name]
            if collection_name:
                db.drop_collection(collection_name)
                msg = f"🧹 Coleção '{collection_name}' deletada de '{database_name}'"
            else:
                client.drop_database(database_name)
                msg = f"💥 Banco de dados '{database_name}' deletado completamente"
            #print(msg)
            return {"status": "success", "message": msg}
        except Exception as e:
            #print(f"❌ Erro ao deletar: {e}")
            return {"status": "error", "message": str(e)}
        finally:
            self.fechar_conexao()
