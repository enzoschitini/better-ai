import streamlit as st

import json
from rich.console import Console
from rich.panel import Panel

from src.agents.files_talk.agent import FileTalkAgent
from src.agents.files_talk.config import AGENT_AI_BANNER

from src.agents.utils.agno_ai_agents import AgnoAiAgents
from src.agents.utils.test_agents.run_agent import RunAgent
from src.utils.unique_id_factory import IDGenerator

class AgnoAgent:
    def __init__(self):
        pass

    def app(self):
        st.title("BetterAI — Agno Agent")
        st.write("### Where Intelligence Finds Purpose")

        agno = AgnoAiAgents()
        agno.register("FileTalkAgent", FileTalkAgent)

        # =========================
        # CREATE
        # =========================
        agent, tool_context = agno.create_agent(
            "FileTalkAgent",
            {
                "session_id": IDGenerator().uuid(),
                "user_id": "user_01",
                "filter_search": {
                    "knowledge_base_id": ["test_agent"]
                }
            }
        )   

        runner = RunAgent(agent=agent)
        ask = st.text_input("Ask something to the agent:")
        response = runner.js_response(ask=ask)

        st.subheader("Agent Response")
        st.write(response["content"])

    def run(self):
        self.app()

if __name__ == "__main__":
    page = AgnoAgent()
    page.run()

# streamlit run src/web_applications/applications/agno_agent.py