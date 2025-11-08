from langchain_community.document_loaders import PyPDFLoader, CSVLoader
import tempfile
import os
import io

class FileEmbeddingProcessor:
    """
    Classe para processar arquivos PDF ou CSV e preparar conteúdo
    para embeddings junto com metadados.
    """

    def __init__(self, file, metadata: dict):
        """
        Args:
            file: UploadFile, BytesIO, ou arquivo local (modo binário).
            metadata (dict): Metadados a associar ao conteúdo.
        """
        self.file = file
        self.metadata = metadata
        self.temp_path = None

    async def _save_temp_file(self):
        """
        Salva o arquivo temporariamente no disco e retorna o caminho.
        Compatível com UploadFile do FastAPI.
        """
        # Determinar extensão (por segurança)
        suffix = os.path.splitext(self.file.filename)[1] if hasattr(self.file, "filename") else ".tmp"

        # Criar arquivo temporário
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)

        # Se for UploadFile, usar leitura assíncrona
        if hasattr(self.file, "read"):
            file_content = await self.file.read()
            temp_file.write(file_content)
        else:
            # Caso seja um objeto tipo BytesIO ou arquivo aberto
            temp_file.write(self.file.read())

        temp_file.close()
        self.temp_path = temp_file.name
        return self.temp_path

    def _load_content(self):
        """Carrega o conteúdo do arquivo conforme o tipo."""
        ext = os.path.splitext(self.temp_path)[1].lower()

        if ext == ".pdf":
            loader = PyPDFLoader(self.temp_path)
        elif ext == ".csv":
            loader = CSVLoader(self.temp_path)
        else:
            raise ValueError(f"❌ Tipo de arquivo não suportado: {ext}")

        documents = loader.load()
        text_content = "\n".join([doc.page_content for doc in documents])
        return text_content

    async def get_embedding_content(self):
        """
        Retorna um dicionário com metadados e conteúdo pronto para embeddings.
        """
        try:
            await self._save_temp_file()
            text_content = self._load_content()

            embedding_content = self.metadata.copy()
            embedding_content["content"] = text_content

            return embedding_content

        finally:
            if self.temp_path and os.path.exists(self.temp_path):
                os.remove(self.temp_path)
