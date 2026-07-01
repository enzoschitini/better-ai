from src.web_applications.pages.knowlegbase_agent.chat import chat
from src.web_applications.pages.knowlegbase_agent.embedding import embedding

from src.utils.unique_id_factory import IDGenerator

id_generator = IDGenerator()

session_id = id_generator.uuid()
user_id = id_generator.timestamp(prefix="streamlit_user", separator="-", as_hex=True, suffix_len=6)
knowledgebase_id = id_generator.timestamp(prefix="kb", separator="-", as_hex=True, suffix_len=6)

chat(session_id=session_id, user_id=user_id, knowledgebase_id=knowledgebase_id)
embedding(job_id=session_id, user_id=user_id, knowledgebase_id=knowledgebase_id)

# Test
# O que estão falando da Copa do Mundo 2026