import os
from typing import List
from supabase import create_client, Client

from dotenv import load_dotenv

load_dotenv()

class SupabaseConnection:
    """Gerencia a conexão com o projeto Supabase."""
    def __init__(self):
        self.url = os.getenv("SUPABASE_URL")
        self.key = os.getenv("SUPABASE_SECRET_KEY")
        
        if not self.url or not self.key:
            raise ValueError("As variáveis de ambiente SUPABASE_URL e SUPABASE_SECRET_KEY são obrigatórias.")
        
        self.client: Client = create_client(self.url, self.key)

class StorageManager:
    """Encapsula operações de manipulação de arquivos no Bucket."""
    def __init__(self, supabase_client: Client, bucket_name: str):
        self.supabase = supabase_client
        self.bucket_name = bucket_name
        self.storage = self.supabase.storage.from_(bucket_name)

    def upload_bytes(self, path_on_storage: str, file_bytes: bytes, content_type: str = "image/jpeg"):
        """Sobe um arquivo para o bucket usando o buffer de bytes."""
        try:
            response = self.storage.upload(
                path=path_on_storage,
                file=file_bytes,
                file_options={"content-type": content_type}
            )
            return response
        except Exception as e:
            print(f"Erro ao fazer upload: {e}")
            return None

    def delete_files(self, paths: List[str]):
        """Remove uma lista de arquivos do bucket."""
        try:
            return self.storage.remove(paths)
        except Exception as e:
            print(f"Erro ao deletar arquivos: {e}")
            return None

    def get_url(self, path: str) -> str:
        """Gera a URL pública de um arquivo."""
        return self.storage.get_public_url(path)


# 1. Inicializa a conexão
conn = SupabaseConnection()

# 2. Instancia o gerenciador para o bucket específico
manager = StorageManager(conn.client, bucket_name="images")

# 3. Exemplo: Upload de um arquivo (simulando bytes)
caminho_local = "storage/mappa_20260204_202404_1.jpg"
nome_no_storage = f"StorageManager/{os.path.basename(caminho_local)}"

def upload_file_example():
    """Exemplo de upload usando bytes."""

    with open(caminho_local, "rb") as f:
        byte_data = f.read()
        upload_res = manager.upload_bytes(nome_no_storage, byte_data)
        
    if upload_res:
        print(f"Upload concluído! URL: {manager.get_url(nome_no_storage)}")

def delete_files_example():
    # 4. Exemplo: Deleção múltipla
    arquivos_para_deletar = [nome_no_storage, "uploads/antigo_01.jpg"]
    del_res = manager.delete_files(arquivos_para_deletar)
    print(f"Status da deleção: {del_res}")

delete_files_example()