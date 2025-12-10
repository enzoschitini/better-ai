from src.embedding_reference.file_content_extractor import FileContentExtractor
from src.embedding_reference.pinecone_vector_store import PineconeClient, PineconeVectorService
from io import BytesIO
import os

ALLOWED_EXTENSIONS = {
    "txt", "md", "markdown", "html",
    "pdf", "doc", "docx", "ppt", "pptx",
    "csv", "xls", "xlsx", "xml", "json"
}

BASE_DIR = "src/embedding_reference/files/"


def load_file_bytes(filename: str):
    """
    Carrega qualquer arquivo da pasta /src/embedding_reference/files/
    e retorna um BytesIO + extensão válida.
    """
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


def extract_file_content(filename: str):
    """
    Carrega arquivo → transforma em BytesIO → extrai conteúdo
    """
    try:
        file_bytes_io, ext = load_file_bytes(filename)
        extractor = FileContentExtractor(file_bytes_io, ext)
        return extractor.extract()

    except Exception as e:
        print(f"❌ Error processing file '{filename}': {e}")
        raise


# ---- TESTE ----
#result = extract_file_content("example.txt")
#print(result)



pine_client = PineconeClient(index_name="backai-vectorstore", namespace="test_namespace", global_namespace="global_namespace")
pine_service = PineconeVectorService(pine_client, embedding_model_name="text-embedding-3-large", dimensions=3072)

embedding_content = """
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

La mia conoscenza dei modelli di Machine Learning deriva dalla mia esperienza come Data 
Scientist e Data Analyst, dove unisco l’approccio analitico alla capacità di tradurre i dati in 
strategie concrete. Laureato all'EBAC, con competenze in statistica, modelli di 
apprendimento automatico, Python, SQL, creazione di dashboard con Streamlit, GitHub, 
Excel, tra gli altri. Sempre alla ricerca di insight nascosti, quei dettagli non sempre evidenti 
ma di immenso valore per il business. 

Ho lavorato anche come sviluppatore Bubble, realizzando siti web, landing page e 
applicazioni complete senza codice, ma con logiche avanzate e un approccio da vero 
sviluppatore software. Nel tempo ho creato piattaforme SaaS, sistemi gestionali, 
marketplace e app educative, integrando API esterne, database complessi e automazioni 
intelligenti. 

Da quando avevo 12 anni, quando ho iniziato a studiare robotica, ho coltivato la mia 
passione per lo sviluppo software. Credo nell'apprendimento pratico e so che, con dedizione, 
impegno e pazienza, è possibile ottenere grandi risultati.  
Oggi rimango motivato a sfidare la mia creatività e cercare nuovi modi per innovare e avere 
un impatto positivo sul mondo che mi circonda.
"""

embedding_metadata = {"user_id": "user_123", "source": "embedding_test.py"}

response = pine_service.generate_vectors(
    text=str(embedding_content),
    metadata=embedding_metadata,
    save_global=False,
    batch_size=200
)

print("✅ Vectors generated and saved to Pinecone:", response)





# python -m src.embedding_reference.embedding_test
"""
extensoes = [
    "txt",
    "md",
    "markdown",
    "html",
    "pdf",
                    "doc", *
    "docx",
                    "ppt", *
    "pptx",
    "csv",
                    "xls", *
    "xlsx",
                    "xml", *
    "json",
]

"""