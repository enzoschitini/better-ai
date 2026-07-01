import os
import mimetypes
from io import BytesIO

import streamlit as st


class FileProcessor:
    def __init__(self):
        pass

    def _load_file(self, path):
        # Implement the logic to load and process the file
        with open(path, "rb") as f:
            file_bytes = BytesIO(f.read())
        return file_bytes

    def get_file_information(self, file):
        name = os.path.basename(file)
        extension = os.path.splitext(name)[1].lstrip(".").lower()
        mime_type, _ = mimetypes.guess_type(file)
        size_bytes = os.path.getsize(file)
        return {
            "name": name,
            "extension": extension,
            "mime_type": mime_type or "application/octet-stream",
            "size_bytes": size_bytes,
            "size_kb": round(size_bytes / 1024, 2),
            "size_mb": round(size_bytes / (1024 * 1024), 4),
            "bytes": self._load_file(file)
        }

    def build_embedding_payload(
        self, 
        job_id: str,
        user_id: str,
        source: str,
        knowledgebase_id: str,
        file_info: dict,
    ):
        payload = {
            "job_id": job_id,

            "identifiers": {
                "user_id": user_id,
            },

            "embedding_metadata": {
                "source": source,
                "knowledgebase_id": knowledgebase_id,
                "origin": "web_app",
            },

            "embedding_settings": {
                "model": "text-embedding-3-large",
                "dimensions": 3072,
                "chunk_size": 500,
                "chunk_overlap": 50,
                "normalize": True,
                "batch_size": 200,
            },

            "vector_db_settings": {
                "save_global": False,
                "main_namespace": "default_main_namespace",
            },

            "file_info": file_info
        }

        return payload


    def embedding_file(self, payload):
        from src.embedding.modules.embedding_file import EmbeddingFile

        embedder = EmbeddingFile(payload)
        embedder._init_tracking()
        result = embedder.run()
        embedder.save()
        return {
            "status": "success",
            "file_id": result["file_id"]
        }


def embedding(job_id: str, user_id: str, knowledgebase_id: str):
    import tempfile

    with st.sidebar:
        st.markdown("### Embedding de Arquivos")

        uploaded_files = st.file_uploader(
            "Selecione um ou mais arquivos",
            type=None,
            accept_multiple_files=True,
        )

        if uploaded_files:
            st.markdown(f"**{len(uploaded_files)} arquivo(s) selecionado(s)**")

            if st.button("Processar Embedding"):
                total = len(uploaded_files)
                progress_bar = st.progress(0, text="Iniciando processamento...")
                status_container = st.container()

                results = []
                embedding_processor = FileProcessor()

                for i, uploaded_file in enumerate(uploaded_files):
                    progress_bar.progress(i / total, text=f"Processando {i + 1}/{total}: **{uploaded_file.name}**")

                    with status_container:
                        status_placeholder = st.empty()
                        status_placeholder.info(f"⏳ Processando: **{uploaded_file.name}**")

                    tmp_path = None
                    try:
                        suffix = os.path.splitext(uploaded_file.name)[1]
                        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                            tmp.write(uploaded_file.read())
                            tmp_path = tmp.name

                        file_info = embedding_processor.get_file_information(tmp_path)
                        file_info["name"] = uploaded_file.name

                        print(f"Initializing KnowledgeBaseAgent runner for job_id={job_id}, user_id={user_id}, knowledgebase_id={knowledgebase_id}...")

                        payload = embedding_processor.build_embedding_payload(
                            job_id=job_id,
                            user_id=user_id,
                            source="uploaded_file",
                            knowledgebase_id=knowledgebase_id,
                            file_info=file_info,
                        )
                        result = embedding_processor.embedding_file(payload)

                        results.append({"name": uploaded_file.name, "status": "success", "file_id": result["file_id"]})
                        status_placeholder.success(f"✅ **{uploaded_file.name}** — File ID: `{result['file_id']}`")

                    except Exception as e:
                        results.append({"name": uploaded_file.name, "status": "error", "error": str(e)})
                        status_placeholder.error(f"❌ **{uploaded_file.name}** — Erro: {e}")

                    finally:
                        if tmp_path and os.path.exists(tmp_path):
                            os.remove(tmp_path)

                progress_bar.progress(1.0, text="Processamento concluído!")

                success_count = sum(1 for r in results if r["status"] == "success")
                error_count = sum(1 for r in results if r["status"] == "error")

                st.divider()
                col1, col2, col3 = st.columns(3)
                col1.metric("Total", total)
                col2.metric("Concluídos", success_count)
                col3.metric("Erros", error_count)



if __name__ == "__main__":
    embedding_processor = FileProcessor()

    file_info = embedding_processor.get_file_information("Credencial Sesc.pdf")
    payload = embedding_processor.build_embedding_payload(
        job_id="job_12345",
        user_id="user_789",
        source="uploaded_file",
        knowledgebase_id="knowledgebase_001",
        file_info=file_info
    )
    result = embedding_processor.embedding_file(payload)

    print("Embedding process completed successfully.")
    print(f"Status: {result['status']}")
    print(f"File ID: {result['file_id']}")

# python -m src.web_applications.pages.knowlegbase_agent.embedding