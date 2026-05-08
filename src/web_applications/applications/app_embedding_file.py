import streamlit as st

from src.utils.unique_id_factory import IDGenerator
from src.embedding.modules.embedding_file import EmbeddingFile

id_gen = IDGenerator()


class AppEmbeddingFile:
    MAX_SIZE_MB = 50

    ALLOWED_EXTENSIONS = {
        "txt", "md", "markdown", "html",
        "pdf", "doc", "docx", "ppt", "pptx",
        "csv", "xls", "xlsx", "xml", "json"
    }

    def __init__(self, knowledge_base_id: str = None):
        self.knowledge_base_id = knowledge_base_id or id_gen.timestamp("kb", "_")

    def _embedding(self, payload: dict):
        embedder = EmbeddingFile(payload)

        embedder._init_tracking()

        response = embedder.run()
        process_metadata = embedder.get_payload()

        return response, process_metadata

    def _upload_files(self):
        uploaded_files = st.file_uploader(
            "Upload files",
            type=list(self.ALLOWED_EXTENSIONS),
            accept_multiple_files=True
        )

        if not uploaded_files:
            return []

        MAX_FILES = 5

        if len(uploaded_files) > MAX_FILES:
            st.error(
                f"Você pode enviar no máximo "
                f"{MAX_FILES} arquivos."
            )
            return []

        valid_files = []

        for uploaded_file in uploaded_files:

            # valida tamanho
            if uploaded_file.size > self.MAX_SIZE_MB * 1024 * 1024:
                st.error(
                    f"{uploaded_file.name} excede "
                    f"{self.MAX_SIZE_MB}MB."
                )
                continue

            file_name = uploaded_file.name

            extension = (
                file_name.split(".")[-1].lower()
                if "." in file_name else ""
            )

            if extension not in self.ALLOWED_EXTENSIONS:
                st.error(
                    f"{file_name}: formato "
                    f"'{extension}' não suportado."
                )
                continue

            file_bytes = uploaded_file.read()

            size_bytes = len(file_bytes)

            file_info = {
                "name": file_name,
                "extension": extension,
                "mime_type": uploaded_file.type,
                "size_bytes": size_bytes,
                "size_kb": round(size_bytes / 1024, 2),
                "size_mb": round(size_bytes / (1024 * 1024), 2),
                "bytes": file_bytes
            }

            valid_files.append(file_info)

        return valid_files

    def app(self):

        st.title("Embedding Files")

        # ---- SESSION STATE ----

        if "embedding_metadata" not in st.session_state:
            st.session_state.embedding_metadata = {"knowledge_base_id": self.knowledge_base_id}

        if "is_embedding" not in st.session_state:
            st.session_state.is_embedding = False

        if "job_id" not in st.session_state:
            st.session_state.job_id = id_gen.timestamp("job", "_")

        # ---- PAYLOAD BASE ----

        base_payload = {
            "job_id": st.session_state.job_id,
            "identifiers": {
                "user_id": "web_app_user"
            }
        }

        # ---- METADATA ----

        """
        with st.expander("Metadata"):

            col1, col2 = st.columns(2)

            with col1:
                key = st.text_input(
                    "Key",
                    value="knowledge_base_id"
                )

            with col2:
                value = st.text_input(
                    "Value",
                    value="my_knowledge_base"
                )

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
                    st.session_state.embedding_metadata = {"knowledge_base_id": self.knowledge_base_id}

            st.subheader("Current Metadata")

            st.json(st.session_state.embedding_metadata)
        """

        # ---- FILES ----

        files = self._upload_files()

        # ---- ACTION ----

        if st.button(
            "Embedding Files",
            disabled=st.session_state.is_embedding
        ):

            if not files:
                st.warning(
                    "Please upload at least one file."
                )
                st.stop()

            st.session_state.is_embedding = True

            progress_bar = st.progress(0)

            status_container = st.container()

            total_files = len(files)

            results = []

            try:

                for index, file_info in enumerate(files):

                    current = index + 1

                    with status_container:

                        with st.status(
                            f"Processing "
                            f"{file_info['name']}...",
                            expanded=True
                        ) as status:

                            payload = {
                                **base_payload,
                                "embedding_metadata": (
                                    st.session_state
                                    .embedding_metadata
                                ),
                                "file_info": file_info
                            }

                            try:

                                result, process_metadata = (
                                    self._embedding(payload)
                                )

                                if (
                                    "file_content"
                                    in process_metadata
                                ):
                                    process_metadata.pop(
                                        "file_content"
                                    )

                                result["metadata"] = (
                                    st.session_state
                                    .embedding_metadata
                                )

                                results.append({
                                    "file": file_info["name"],
                                    "status": "success",
                                    "result": result
                                })

                                status.update(
                                    label=(
                                        f"{file_info['name']} "
                                        f"completed"
                                    ),
                                    state="complete"
                                )

                            except Exception as e:

                                results.append({
                                    "file": file_info["name"],
                                    "status": "error",
                                    "error": str(e)
                                })

                                status.update(
                                    label=(
                                        f"{file_info['name']} "
                                        f"failed"
                                    ),
                                    state="error"
                                )

                    progress = current / total_files

                    progress_bar.progress(progress)

                st.success(
                    "Embedding queue finished."
                )

                #st.subheader("Results")
                #st.json(results)

            finally:
                st.session_state.is_embedding = False

    def run(self):
        self.app()


if __name__ == "__main__":
    page = AppEmbeddingFile()
    page.run()

# streamlit run src/web_applications/applications/app_embedding_file.py