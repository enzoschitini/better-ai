import streamlit as st

from src.utils.unique_id_factory import IDGenerator

if "knowlegbase_session_ids" not in st.session_state:
    id_generator = IDGenerator()
    st.session_state.knowlegbase_session_ids = {
        "session_id": id_generator.uuid(),
        "user_id": id_generator.timestamp(prefix="streamlit_user", separator="-", as_hex=True, suffix_len=6),
        "knowledgebase_id": id_generator.timestamp(prefix="kb", separator="-", as_hex=True, suffix_len=6),
    }

session_id = st.session_state.knowlegbase_session_ids["session_id"]
user_id = st.session_state.knowlegbase_session_ids["user_id"]
knowledgebase_id = st.session_state.knowlegbase_session_ids["knowledgebase_id"]

# Lazy imports keep first page load fast and avoid loading heavy dependencies
# when the page is not opened.
from src.web_applications.pages.knowlegbase_agent.chat import chat
from src.web_applications.pages.knowlegbase_agent.embedding import embedding

chat(session_id=session_id, user_id=user_id, knowledgebase_id=knowledgebase_id)
embedding(job_id=session_id, user_id=user_id, knowledgebase_id=knowledgebase_id)