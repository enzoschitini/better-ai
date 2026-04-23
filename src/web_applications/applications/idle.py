import streamlit as st
from src.web_applications.utils.render_components import Component

class Idle:
    def __init__(self):
        self.component = Component()

    def head(self):
        self.component.image("images/idle.png", width=150)
        st.write("")

        self.component.text("Agent Idle", size=50, weight=600, align="center")
        self.component.text("Ask your agent to do something!", size=30, align="center")
    
    def run(self):
        self.head()

if __name__ == "__main__":
    page = Idle()
    page.run()

# streamlit run chat.py
# streamlit run src/web_applications/applications/idle.py