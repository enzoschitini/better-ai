import os
from dotenv import load_dotenv
from io import BytesIO

from src.embedding.file_content_extractor import FileContentExtractor
from src.embedding.pinecone_vector_store import PineconeClient, PineconeVectorService
from src.embedding.tokens_calculator.cost import EmbeddingCostCalculator

load_dotenv()

def payload_validation():
    # 1. Valutazione delle informazioni (L'ID dell'archivio può venire vuoto, in questo caso tocca a betterai crearlo)
    pass

def file_from_bites(filename: str): # 2. Transforma l'archivio in BitesIO
    """
    Carrega qualquer arquivo da pasta /src/embedding_reference/files/
    e retorna um BytesIO + extensão válida.
    """

    ALLOWED_EXTENSIONS = {
        "txt", "md", "markdown", "html",
        "pdf", "doc", "docx", "ppt", "pptx",
        "csv", "xls", "xlsx", "xml", "json"
    }

    BASE_DIR = "src/embedding_reference/files/"

    file_path = os.path.join(BASE_DIR, filename)

    # Valida caminho
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Arquivo não encontrado: {file_path}")

    # Valida extensão
    ext = filename.lower().split(".")[-1]
    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Extensão não suportada: .{ext}")

    # Lê bytes
    with open(file_path, "rb") as f:
        file_bytes = f.read()

    # Transforma em BytesIO
    file_bytes_io = BytesIO(file_bytes)

    return file_bytes_io, ext

def extract_file_content(file_bytes, file_extension):
    # 3. Estrarre il contenuto
    """
    Carrega arquivo → transforma em BytesIO → extrai conteúdo
    """
    try:
        extractor = FileContentExtractor(file_bytes, file_extension)
        return extractor.extract()

    except Exception as e:
        print(f"❌ Error processing file '{filename}': {e}")
        raise

def transform_embedding_data(self, file_process, file_extension):
    # Preparazione dei dati per l'embedding
    try:
        #logger.debug("Preparando dados para embeddings...")

        if "usage_metadata" in file_process.get("response", {}):
            file_content = file_process["response"]["file_content"]
            #logger.debug("Uso de metadata detectado: %s", file_process["response"]["usage_metadata"])
        else:
            file_content = file_process["response"]

        embedding_content = {
            "file_name": self.sqs_message_body["metadata"]["st_name"],
            "file_url": f"{os.getenv('S3_DOMAIN')}{self.sqs_message_body['fileUrl']}",
            "file_content": file_content
        }

        #logger.info("Dados para embedding preparados com sucesso.")

    except Exception as e:
        #logger.error("Erro ao transformar dados para embedding : %s. jobId: %s, fileId: %s", e, self.sqs_message_body["jobId"], self.sqs_message_body["fileId"])
        raise

    return embedding_content

def embedding_cost(content):
    # Calcola i costi
    calc = EmbeddingCostCalculator("text-embedding-3-large")
    resultado = calc.calculate_cost_json(content)

    pass

def business_validation():
    # Verifica se l'utente ha ancora dei crediti
    pass

def embedding(embedding_content, embedding_metadata):
    # Si fa l'embedding

    pine_client = PineconeClient(index_name="backai-vectorstore", 
                                 namespace="test_namespace", global_namespace="global_namespace")
    
    pine_service = PineconeVectorService(pine_client, embedding_model_name="text-embedding-3-large", dimensions=3072)

    response = pine_service.generate_vectors(
        text=str(embedding_content),
        metadata=embedding_metadata,
        save_global=False,
        batch_size=200
    )

    return response

def save_process():
    # Salva l'operazione sul MongoDB
    pass

def _EmbeddingExecute():
    # Flusso completo
    pass

"""
python -m src.embedding.embedding_module

payload = {
    "fileId": "21d75dca2eec7b02080327f40220e20dxx2.pdf",
    "fileName": "name file.pdf",
    "fileUrl": "https://domain.com/docs/21d75dca2eec7b02080327f40220e20dxx2.pdf" (Opzionale)

    "embedding_settings": {
        "llm_model": "text-embedding-3-large",
        "dimensions": 3072
    },
    
    "metadata": {
        "id_collection": "id_collection_01",
        "id_series": "id_series_01",
        "id_client": "id_client_01",
        "id_user": "id_user_01",
        "id_workspace": "id_workspace_01"
    }
}

+ File

1. Valutazione delle informazioni (L'ID dell'archivio può venire vuoto, in questo caso tocca a betterai crearlo)
2. Transforma l'archivio in BitesIO

3. Estrarre il contenuto
3.1 Calcola i costi
3.2 Verifica se l'utente ha ancora dei crediti

4. Preparazione dei dati per l'embedding
5. Si fa l'embedding
6. Calcola i costi
7. Salva l'operazione sul MongoDB
8. Ritorna i parametri

payload = {
    "status": "success",
    "message": "File embedded",
    "metadata": {
        "fileId": "21d75dca2eec7b02080327f40220e20dxx2.pdf",
        "mongoId": "83720083721",
    }
}
"""











