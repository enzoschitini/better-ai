import os
import uuid

from src.embbeding.document_scraper import FileEmbeddingProcessor
from src.embbeding.pinecone_crud import PineconeCRUD

def embedding_documents(metadata_dict, file_content, file):
    # Extract filename and extension
    file_name, file_extension = os.path.splitext(file.filename)
    file_extension = file_extension.replace('.', '')

    # Ensure required structure exists in metadata
    metadata_dict.setdefault("embedding_filter", {})
    metadata_dict.setdefault("embedding_aggregations", {})

    # Generate unique file_id if missing
    if not metadata_dict["embedding_filter"].get("file_id"):
        metadata_dict["embedding_filter"]["file_id"] = str(uuid.uuid4())

    # Update metadata with extracted file information
    metadata_dict["embedding_aggregations"].update({
        "file_name": file_name,
        "file_extension": file_extension
    })

    # Processar arquivo para embeddings
    processor = FileEmbeddingProcessor(file=file, file_bytes=file_content, metadata=metadata_dict)
    result = str(processor.get_embedding_content())

    crud = PineconeCRUD(namespace="betterai-embeddings")
    
    crud.create_from_text(
        raw_text=result,
        metadata=metadata_dict["embedding_filter"]
    )

    embedding_result = {
        "status": "success",
        "message": "Done"
    }

    return embedding_result








