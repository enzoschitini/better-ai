import os
from dotenv import load_dotenv

from src.embedding.file_content_extractor import FileContentExtractor
from src.embedding.pinecone_vector_store import PineconeClient, PineconeVectorService
from src.embedding.tokens_calculator.cost import EmbeddingCostCalculator

load_dotenv()

"""
python -m src.embedding.embedding_module

payload = {
    "fileId": "21d75dca2eec7b02080327f40220e20dxx2.pdf",
    "fileName": "name file.pdf",

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











