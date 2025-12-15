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

def file_from_bytes(file): # 2. Transforma l'archivio in BitesIO
    """
    Recebe um UploadFile (FastAPI),
    valida a extensão e retorna:
    - filename
    - extensão
    - BytesIO
    """

    ALLOWED_EXTENSIONS = {
        "txt", "md", "markdown", "html",
        "pdf", "doc", "docx", "ppt", "pptx",
        "csv", "xls", "xlsx", "xml", "json"
    }

    # Nome do arquivo
    filename = file.filename

    if not filename or "." not in filename:
        raise ValueError("Nome de arquivo inválido")

    # Extensão
    ext = filename.lower().split(".")[-1]

    if ext not in ALLOWED_EXTENSIONS:
        raise ValueError(f"Extensão não suportada: .{ext}")

    # Lê os bytes do UploadFile
    file_bytes = file.file.read()

    if not file_bytes:
        raise ValueError("Arquivo vazio")

    # Converte para BytesIO
    file_bytes_io = BytesIO(file_bytes)

    return filename, ext, file_bytes_io

def extract_file_content(file_bytes, file_extension):
    # 3. Estrarre il contenuto
    """
    Carrega arquivo → transforma em BytesIO → extrai conteúdo
    """
    try:
        extractor = FileContentExtractor(file_bytes, file_extension)
        return extractor.extract()

    except Exception as e:
        filename = "filename"
        print(f"❌ Error processing file '{filename}': {e}")
        raise

def transform_embedding_data(filename, file_content):
    # Preparazione dei dati per l'embedding
    try:
        #logger.debug("Preparando dados para embeddings...")

        embedding_content = {
            "file_name": filename,
            "file_url": "https://test.com",
            "file_content": file_content
        }

        #logger.info("Dados para embedding preparados com sucesso.")

        return embedding_content

    except Exception as e:
        #logger.error("Erro ao transformar dados para embedding : %s. jobId: %s, fileId: %s", e, self.sqs_message_body["jobId"], self.sqs_message_body["fileId"])
        raise

def embedding_cost(content):
    try:
        # Calcola i costi
        calc = EmbeddingCostCalculator("text-embedding-3-large")
        response = calc.calculate_cost_json(content)

        return response

    except Exception as e:
        raise

def business_validation():
    # Verifica se l'utente ha ancora dei crediti
    pass

def embedding(embedding_content, embedding_metadata):
    try:
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

    except Exception as e:
        raise

def save_process():
    # Salva l'operazione sul MongoDB
    pass

def EmbeddingExecute():
    # Fluxo 
    filename = "Candidatura.pdf"
    ext = "pdf"
    text = """
    Sono uno sviluppatore con 4 anni di esperienza in progetti che combinano prestazioni, 
    scalabilità e best practice.

    Sono un esperto di Intelligenza Artificiale, Machine Learning e dati, con una solida 
    esperienza nello sviluppo di applicazioni complete e scalabili. 

    Negli ultimi anni ho lavorato su diversi progetti in diversi settori, tra cui intelligenza artificiale, 
    ho seguito da vicino l’evoluzione dell’AI Generativa, partendo dai primi esperimenti con gli AI 
    Agents fino allo sviluppo di sistemi complessi di orchestrazione e automazione. Progettando 
    architetture RAG, orchestrando modelli LLM e integrato strumenti come LangChain, 
    LlamaIndex, Crewai e Dify per creare agenti intelligenti in grado di ragionare, pianificare e 
    interagire in modo autonomo. 
    """

    embedding_content = transform_embedding_data(filename, text)
    cost = embedding_cost(str(embedding_content))

    return cost

print(EmbeddingExecute())
"""
python -m src.embedding.embedding_module

payload = {
    "fileId": "21d75dca2eec7b02080327f40220e20dxx2.pdf",
    "fileName": "name file.pdf",
    "fileUrl": "https://domain.com/docs/21d75dca2eec7b02080327f40220e20dxx2.pdf" (Opzionale)

    "embedding_settings": {
        "llm_model": "text-embedding-3-large",
        "dimensions": 3072,
        "global_namespace": True,
        "batch_size": 200
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











