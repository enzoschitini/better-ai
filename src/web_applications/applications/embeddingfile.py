import streamlit as st
from src.utils.unique_id_factory import IDGenerator
from src.embedding.modules.embedding_file import EmbeddingFile

id_gen = IDGenerator()
job_id = id_gen.timestamp("job", "_")

class Embeddingfile:
    def __init__(self):
        pass

    def _embedding(self, payload: dict):
        embedder = EmbeddingFile(payload)
        embedder._init_tracking()
        response = embedder.run()
        embedder.save()

        return response

    def _upload_file(self):
        uploaded_file = st.file_uploader("Upload file")

        if uploaded_file is None:
            return None

        file_bytes = uploaded_file.read()

        size_bytes = len(file_bytes)
        size_kb = round(size_bytes / 1024, 2)
        size_mb = round(size_kb / 1024, 2)

        file_name = uploaded_file.name
        extension = file_name.split(".")[-1] if "." in file_name else ""

        file_info = {
            "name": file_name,
            "extension": extension,
            "mime_type": uploaded_file.type,
            "size_bytes": size_bytes,
            "size_kb": size_kb,
            "size_mb": size_mb,
            "bytes": file_bytes
        }

        return file_info

    def app(self):
        st.title("Embedding File")

        payload = {
            "job_id": job_id,
            "identifiers": {"user_id": "web_app_user"}
        }

        with st.expander("Metadata"):
            col1, col2 = st.columns(2)

            with col1:
                key = st.text_input("Key")

            with col2:
                value = st.text_input("Value")
            
            embedding_metadata = {}
            
            if st.button("ADD"):
                embedding_metadata[key] = value
            
            payload["embedding_metadata"] = embedding_metadata
        
        file_info = self._upload_file()

        if file_info:
            payload["file_info"] = file_info
        
        # inicializa estado
        if "is_embedding" not in st.session_state:
            st.session_state.is_embedding = False

        if st.button("Embedding File", disabled=st.session_state.is_embedding):
            if file_info is None:
                st.warning("Please upload a file before embedding.")
                st.stop()

            st.session_state.is_embedding = True

            try:
                with st.spinner("Embedding in progress..."):
                    result = self._embedding(payload)
                    result["metadata"] = embedding_metadata

                st.success("Embedding flow completed successfully")

                with st.expander("Informations"):
                    st.write(result)

            finally:
                st.session_state.is_embedding = False

    def run(self):
        self.app()

if __name__ == "__main__":
    page = Embeddingfile()
    page.run()

# streamlit run src/web_applications/applications/embeddingfile.py