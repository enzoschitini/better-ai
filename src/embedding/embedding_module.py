import os
from dotenv import load_dotenv
from io import BytesIO
from decimal import Decimal

from src.chat.utils.mongo_manage import MongoDBManager
from src.embedding.file_content_extractor import FileContentExtractor
from src.embedding.pinecone_vector_store import PineconeClient, PineconeVectorService
from src.embedding.tokens_calculator.cost import EmbeddingCostCalculator

load_dotenv()

payload = {
    "company_id": "1",
    "fileId": "21d75dca2eec7b02080327f40220e20dxx2.pdf",
    "fileName": "name file.pdf",
    "fileUrl": "https://domain.com/docs/21d75dca2eec7b02080327f40220e20dxx2.pdf", # (Opzionale)
    
    "metadata": { # (Opzionale)
        "filters": {
            "id_collection": "id_collection_01",
            "id_series": "id_series_01",
            "id_client": "id_client_01",
            "id_user": "id_user_01",
            "id_workspace": "id_workspace_01"
        },
        "aditional_informatios": {
            "Collection Name:": "BetterAI Repo"
        }
    },

    "embedding_settings": { # (Opzionale)
        "llm_model": "text-embedding-3-large",
        "dimensions": 3072,
        "global_namespace": True,
        "batch_size": 200
    }
}

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

        embedding_metadata = {
            "fileIDD": "1"
        }

        embedding_content = {
            "file_name": filename,
            "file_url": "https://test.com",
            "file_content": file_content
        }

        #logger.info("Dados para embedding preparados com sucesso.")

        return embedding_content, embedding_metadata

    except Exception as e:
        #logger.error("Erro ao transformar dados para embedding : %s. jobId: %s, fileId: %s", e, self.sqs_message_body["jobId"], self.sqs_message_body["fileId"])
        raise

def embedding_cost(content):
    try:
        # Calcola i costi
        calc = EmbeddingCostCalculator("text-embedding-3-large")
        cost = calc.calculate_cost_json(content)
        response = {
            "embedding_cost": cost
        }

        return response

    except Exception as e:
        raise

# Classe separata:
def business_validation(plan: dict, operation: dict) -> bool:
    """
    Retorna True se o plano possuir créditos suficientes
    tanto em custo (USD) quanto em tokens.

print("\nInformações do plano da empresa (No banco)")
print(json.dumps(business["plan"], indent=4))
print("\nInformações do custo previsto para a operação")
print(json.dumps(embedding_cost, indent=4))

print(
    business_validation(
        plan=business["plan"],
        operation=embedding_cost
    )
)
    """

    # ===== CUSTO (USD) =====
    budget_usd = Decimal(plan["resorce"]["cost"]["monthly_budget_total_cost_usd"])
    used_usd = Decimal(plan["cost"]["total_cost_usd"])
    operation_usd = Decimal(operation["embedding_cost"]["total_cost"]["cost_usd"])

    has_usd_credit = (budget_usd - used_usd) >= operation_usd

    # ===== TOKENS =====
    budget_tokens = plan["resorce"]["tokens"]["monthly_budget_total_tokens"]
    used_tokens = plan["tokens"]["total_tokens"]
    operation_tokens = operation["embedding_cost"]["tokens"]

    has_token_credit = (budget_tokens - used_tokens) >= operation_tokens

    return has_usd_credit and has_token_credit



def business_update_usage():
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

def save_process(payload:dict, aggregates:list):
    # Salva l'operazione sul MongoDB

    mongo = MongoDBManager()

    for agg in aggregates:
        for key in agg.keys():
            payload[key] = agg[key]
    
    mongo_id = mongo.salvar_payload(database_name="embeddings", collection_name="betterai_embeddings", payload=payload)
    
    return mongo_id, payload

def EmbeddingExecute():
    # Fluxo 
    # file_from_bytes -> filename, ext, file_bytes_io
    # extract_file_content -> text

    filename = "Candidatura.pdf"
    ext = "pdf"
    text = """
    Negli ultimi anni ho lavorato su diversi progetti in diversi settori, tra cui intelligenza artificiale, 
    ho seguito da vicino l’evoluzione dell’AI Generativa, partendo dai primi esperimenti con gli AI 
    Agents fino allo sviluppo di sistemi complessi di orchestrazione e automazione. Progettando 
    architetture RAG, orchestrando modelli LLM e integrato strumenti come LangChain, 
    LlamaIndex, Crewai e Dify per creare agenti intelligenti in grado di ragionare, pianificare e 
    interagire in modo autonomo. 
    """

    embedding_content, embedding_metadata = transform_embedding_data(filename, text)
    cost = embedding_cost(str(embedding_content))

    print(business_validation(1))

    if business_validation(0):
        vectorstore_embedding = embedding(embedding_content, embedding_metadata)
        
        mongo_id, mongo_payload = save_process(payload, [cost, {"vectorstore_informations": vectorstore_embedding["embedding_informations"]}])

        return mongo_id
    

print(EmbeddingExecute())
"""
python -m src.embedding.embedding_module

payload = {
    "fileId": "21d75dca2eec7b02080327f40220e20dxx2.pdf",
    "fileName": "name file.pdf",
    "fileUrl": "https://domain.com/docs/21d75dca2eec7b02080327f40220e20dxx2.pdf", # (Opzionale)
    
    "metadata": { # (Opzionale)
        "filters": {
            "id_collection": "id_collection_01",
            "id_series": "id_series_01",
            "id_client": "id_client_01",
            "id_user": "id_user_01",
            "id_workspace": "id_workspace_01"
        },
        "aditional_informatios": {
            "Collection Name:": "BetterAI Repo"
        }
    },

    "embedding_settings": { # (Opzionale)
        "llm_model": "text-embedding-3-large",
        "dimensions": 3072,
        "global_namespace": True,
        "batch_size": 200
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











