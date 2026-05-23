import streamlit as st

import json
from rich.console import Console
from rich.panel import Panel

from agents.legacy.files_talk.agent import FileTalkAgent
from agents.legacy.files_talk.config import AGENT_AI_BANNER

from src.agents.utils.agno_ai_agents import AgnoAiAgents
from src.agents.utils.test_agents.run_agent import RunAgent
from src.utils.unique_id_factory import IDGenerator

class AgnoAgent:
    def __init__(self, filter_search: dict = None):
        self.filter_search = filter_search or {
            "knowledge_base_id": ["test_agent"]
        }

    def app(self):
        st.title("ChatAI - Talk to your data")
        st.info(
            "Bem-vindo(a) ao ChatAI! Faça o upload dos seus arquivos e converse com eles de forma inteligente!"
        )

        st.divider()

        agno = AgnoAiAgents()
        agno.register("FileTalkAgent", FileTalkAgent)

        # =========================
        # CREATE
        # =========================
        #st.write(self.filter_search)
        agent, tool_context = agno.create_agent(
            "FileTalkAgent",
            {
                "session_id": IDGenerator().uuid(),
                "user_id": "user_01",
                "filter_search": self.filter_search
            }
        ) 

        # Inicializa histórico
        if "messages" not in st.session_state:
            st.session_state.messages = []

        runner = RunAgent(agent=agent)

        # Mostrar histórico
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        # Input do usuário
        if prompt := st.chat_input("Digite sua mensagem..."):
            # Salva mensagem do usuário
            st.session_state.messages.append({
                "role": "user",
                "content": prompt
            })

            # Mostra mensagem do usuário
            with st.chat_message("user"):
                st.markdown(prompt)

            # Gera resposta fake
            response = runner.js_response(ask=prompt)
            content = response["content"]
            
            #print(f"{json.dumps(tool_context.tool_responser.get_metadata(), indent=4, ensure_ascii=False)}")

            # Salva resposta
            st.session_state.messages.append({
                "role": "assistant",
                "content": content
            })

            # Mostra resposta
            with st.chat_message("assistant"):
                st.markdown(content)


    def run(self):
        self.app()

if __name__ == "__main__":
    page = AgnoAgent()
    page.run()

# streamlit run src/web_applications/applications/agno_agent.py