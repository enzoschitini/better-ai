import json
import time

from io import BytesIO
from pathlib import Path
from src.embedding.modules.embedding_file import EmbeddingFile
from src.utils.unique_id_factory import IDGenerator

id_gen = IDGenerator()

def generate_payload(file_path: Path):
    with open(file_path, "rb") as f:
        file_bytes = BytesIO(f.read())

    file_size_bytes = file_path.stat().st_size

    payload = {
        "job_id": id_gen.timestamp(prefix="job"),

        "embedding_metadata": {
            "collection_id": "oboticario"
        },

        "embedding_settings": {
            "model": "text-embedding-3-large",
            "dimensions": 3072,
            "chunk_size": 500,
            "chunk_overlap": 50,
            "normalize": True,
            "batch_size": 200,
        },

        "file_info": {
            "name": file_path.name,
            "extension": file_path.suffix.lstrip("."),
            "mime_type": "application/pdf",
            "size_bytes": file_size_bytes,
            "size_kb": round(file_size_bytes / 1024, 2),
            "size_mb": round(file_size_bytes / (1024 * 1024), 2),
            "bytes": file_bytes
        }
    }

    return payload


folder = Path("src/agents/rag_agent/pdfs/oboticario")
files = list(folder.glob("*.pdf"))
#files = files[:2]  # Process only the first 2 files for testing

print(f"Found {len(files)} PDF files\n")

for i, file in enumerate(files):
    print(f"[{i+1}/{len(files)}] Processing: {file.name}")

    try:
        payload = generate_payload(file)

        embedder = EmbeddingFile(payload)
        embedder._init_tracking()
        embedder.run()
        embedder.save()

        print(f"  ✓ Done: {file.name}")

    except Exception as e:
        print(f"  ✗ Error on {file.name}: {e}")

    if i < len(files) - 1:  # Skip sleep after last file
        time.sleep(2)

print("\nAll files processed.")

# python -m src.agents.rag_agent.tools.embedding_content_agent