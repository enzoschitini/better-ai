from langchain_community.document_loaders import PyPDFLoader, CSVLoader
import tempfile
import os
import io

class FileEmbeddingProcessor:
    """
    Classe para processar arquivos PDF ou CSV e preparar conteúdo
    para embeddings junto com metadados.
    """

    def __init__(self, file, metadata: dict, file_bytes: bytes = None):
        """
        Args:
            file: Objeto de arquivo (ex.: UploadFile, BytesIO ou file-like).
            metadata (dict): Metadados a associar ao conteúdo.
            file_bytes (bytes, opcional): Conteúdo em bytes (necessário para UploadFile assíncrono).
        """
        self.file = file
        self.metadata = metadata
        self.file_bytes = file_bytes
        self.temp_path = None

    def _save_temp_file(self):
        """Salva o arquivo temporariamente no disco e retorna o caminho."""
        # Se for UploadFile, usamos o nome diretamente
        suffix = os.path.splitext(self.file.filename if hasattr(self.file, "filename") else self.file.name)[1]

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        
        # Se já temos bytes do arquivo (como em UploadFile)
        if self.file_bytes:
            temp_file.write(self.file_bytes)
        else:
            # Caso contrário, lemos diretamente (para open() normal)
            temp_file.write(self.file.read())
        
        temp_file.close()
        self.temp_path = temp_file.name
        return self.temp_path

    def _load_content(self):
        """Carrega conteúdo do arquivo conforme o tipo."""
        ext = os.path.splitext(self.temp_path)[1].lower()

        if ext == ".pdf":
            loader = PyPDFLoader(self.temp_path)
        elif ext == ".csv":
            loader = CSVLoader(self.temp_path)
        else:
            raise ValueError(f"❌ Tipo de arquivo não suportado: {ext}")

        documents = loader.load()
        text_content = "".join([doc.page_content for doc in documents])
        return text_content

    def get_embedding_content(self):
        """
        Retorna um dicionário com metadados e conteúdo pronto para embeddings.
        """
        try:
            self._save_temp_file()
            text_content = self._load_content()

            embedding_content = self.metadata.copy()
            embedding_content["content"] = text_content

            return embedding_content

        finally:
            # Remove o arquivo temporário
            if self.temp_path and os.path.exists(self.temp_path):
                os.remove(self.temp_path)


"""
# Exemplo de uso (com arquivo local)
with open("src/embbeding/files/example.csv", "rb") as f:
    metadata = {"author": "Fredric Brown", "category": "sci-fi"}
    processor = FileEmbeddingProcessor(file=f, metadata=metadata)
    result = processor.get_embedding_content()

print(result["author"])  # -> dict com metadados + 'content'
#"""
