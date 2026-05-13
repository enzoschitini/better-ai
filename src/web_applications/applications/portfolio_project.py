import streamlit as st
from src.web_applications.applications.agno_agent import AgnoAgent
from src.web_applications.applications.app_embedding_file import AppEmbeddingFile
from src.utils.unique_id_factory import IDGenerator

class PortfolioProject:
    def __init__(self):
        self.generate_id = IDGenerator()

    def app(self):
        if "knowledge_base_id" not in st.session_state:
            st.session_state.knowledge_base_id = (
                self.generate_id.timestamp("kb", "_")
            )

        knowledge_base_id = st.session_state.knowledge_base_id

        embed = AppEmbeddingFile(knowledge_base_id=knowledge_base_id)
        agent = AgnoAgent(filter_search={"knowledge_base_id": [knowledge_base_id]})

        agent.run()

        with st.sidebar:
            embed.run()
            #st.write(knowledge_base_id)
        

    def run(self):
        self.app()

if __name__ == "__main__":
    page = PortfolioProject()
    page.run()

# streamlit run src/web_applications/applications/portfolio_project.py