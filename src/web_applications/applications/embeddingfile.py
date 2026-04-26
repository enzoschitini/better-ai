import streamlit as st
from src.utils.unique_id_factory import IDGenerator

id_gen = IDGenerator()
job_id = id_gen.timestamp("job", "_")

class Embeddingfile:
    def __init__(self):
        pass

    def app(self):
        st.title("Embedding File")

        payload = {
            "job_id": job_id,
            "identifiers": {"user_id": "web_app_user"}
        }

        col1, col2 = st.columns(2)

        with col1:
            key = st.text_input("Key")

        with col2:
            value = st.text_input("Value")
        
        embedding_metadata = {}
        
        if st.button("ADD"):
            embedding_metadata[key] = value
        
        payload["embedding_metadata"] = embedding_metadata

        st.write(payload)

    def run(self):
        self.app()

if __name__ == "__main__":
    page = Embeddingfile()
    page.run()

# streamlit run src/web_applications/applications/embeddingfile.py