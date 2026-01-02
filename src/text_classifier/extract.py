import asyncio
from types import SimpleNamespace # Used to create a quick object with attributes
from src.embedding.services.file_content_extractor import FileContentExtractor
from src.embedding.embedding_module import FileService

async def main():
    # 1. Load file
    file_path = "src/text_classifier/txt_examples/n8n.txt"

    with open(file_path, "rb") as f:
        file_content = f.read()

    # 2. Wrap the bytes so they have a .filename attribute
    # This mimics the UploadFile object the service expects
    mock_file = SimpleNamespace(
        filename="n8n.txt",
        file=file_content
    )

    # 3. Call the service
    # Note: If FileService.load reads from .file internally, this will work.
    # If it expects the object itself to be the file, pass mock_file.
    file_name, file_extension, file_bytes = await FileService.load(mock_file)
    
    print(f"Successfully processed: {file_name} with extension {file_extension}")

if __name__ == "__main__":
    asyncio.run(main())

# python -m src.text_classifier.extract











