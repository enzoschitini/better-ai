import streamlit as st
from src.utils.unique_id_factory import IDGenerator
from src.embedding.modules.embedding_file import EmbeddingFile

id_gen = IDGenerator()


class Embeddingfile:
    def __init__(self):
        pass

    def _embedding(self, payload: dict):
        embedder = EmbeddingFile(payload)
        embedder._init_tracking()
        response = embedder.run()
        process_metadata = embedder.get_payload()

        return response, process_metadata

    def _upload_file(self):
        MAX_SIZE_MB = 50
        ALLOWED_EXTENSIONS = {
            "txt", "md", "markdown", "html",
            "pdf", "doc", "docx", "ppt", "pptx",
            "csv", "xls", "xlsx", "xml", "json"
        }

        uploaded_file = st.file_uploader(
            "Upload file",
            type=list(ALLOWED_EXTENSIONS),
            max_upload_size=MAX_SIZE_MB
        )

        if uploaded_file is None:
            return None

        # valida tamanho ANTES de ler
        if uploaded_file.size > MAX_SIZE_MB * 1024 * 1024:
            st.error(f"O arquivo excede o limite de {MAX_SIZE_MB}MB.")
            return None

        file_name = uploaded_file.name
        extension = file_name.split(".")[-1].lower() if "." in file_name else ""

        if extension not in ALLOWED_EXTENSIONS:
            st.error(f"Formato '{extension}' não suportado.")
            return None

        file_bytes = uploaded_file.read()

        size_bytes = len(file_bytes)
        size_kb = size_bytes / 1024
        size_mb = size_bytes / (1024 * 1024)

        file_info = {
            "name": file_name,
            "extension": extension,
            "mime_type": uploaded_file.type,
            "size_bytes": size_bytes,
            "size_kb": round(size_kb, 2),
            "size_mb": round(size_mb, 2),
            "bytes": file_bytes
        }

        return file_info

    def app(self):
        st.title("Embedding File")

        # ---- SESSION STATE ----
        if "embedding_metadata" not in st.session_state:
            st.session_state.embedding_metadata = {}

        if "is_embedding" not in st.session_state:
            st.session_state.is_embedding = False

        if "job_id" not in st.session_state:
            st.session_state.job_id = id_gen.timestamp("job", "_")

        payload = {
            "job_id": st.session_state.job_id,
            "identifiers": {"user_id": "web_app_user"}
        }

        # ---- METADATA UI ----
        with st.expander("Metadata"):
            col1, col2 = st.columns(2)

            with col1:
                key = st.text_input("Key", value="knowledge_base_id")

            with col2:
                value = st.text_input("Value", value="my_knowledge_base")

            col_add, col_clear = st.columns(2)

            with col_add:
                if st.button("ADD"):
                    if not key:
                        st.warning("Key cannot be empty")
                    elif not value:
                        st.warning("Value cannot be empty")
                    else:
                        st.session_state.embedding_metadata[key] = value

            with col_clear:
                if st.button("CLEAR"):
                    st.session_state.embedding_metadata = {}

            payload["embedding_metadata"] = st.session_state.embedding_metadata

            st.subheader("Current Metadata")
            st.json(st.session_state.embedding_metadata)

        # ---- UPLOAD ----
        file_info = self._upload_file()

        if file_info:
            payload["file_info"] = file_info

        # ---- ACTION ----
        if st.button("Embedding File", disabled=st.session_state.is_embedding):
            if file_info is None:
                st.warning("Please upload a file before embedding.")
                st.stop()

            st.session_state.is_embedding = True

            try:
                with st.spinner("Embedding in progress..."):
                    result, process_metadata = self._embedding(payload)

                    if "file_content" in process_metadata:
                        process_metadata.pop("file_content")

                    result["metadata"] = st.session_state.embedding_metadata

                st.success("Embedding flow completed successfully")

                with st.expander("Informations"):
                    st.json(result)

                with st.expander("Process Metadata"):
                    st.json(process_metadata)

            finally:
                st.session_state.is_embedding = False

    def run(self):
        self.app()

if __name__ == "__main__":
    page = Embeddingfile()
    page.run()

# streamlit run src/web_applications/applications/embeddingfile.py