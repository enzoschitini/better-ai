import streamlit as st
from src.web_applications.utils.render_components import Component

class Idle:
    def __init__(self):
        self.component = Component()
    
    def _reset_chat(self):
        if "messages" in st.session_state:
            del st.session_state.messages
    
    def head(self):
        self.component.image("images/idle.png", width=150)
        st.write("")

        #self.component.text("Agent Idle", size=50, weight=600, align="center")
        self.component.text("Ask your agent to do something!", size=30, align="center")

    def page(self):
        # Inicializa histórico
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Função de resposta fake
        def get_fake_response(user_input):
            user_input = user_input.lower()

            if "oi" in user_input:
                return "Olá! Como posso te ajudar hoje?"
            elif "preço" in user_input:
                return "Os preços começam a partir de R$ 99/mês."
            elif "produto" in user_input:
                return "Temos vários produtos disponíveis! Quer ver algum específico?"
            else:
                return "Interessante... me conte mais!"

        # 👇 PRIMEIRO: captura input e atualiza estado
        if prompt := st.chat_input("Digite sua mensagem..."):

            st.session_state.messages.append({
                "role": "user",
                "content": prompt
            })

            response = get_fake_response(prompt)

            st.session_state.messages.append({
                "role": "assistant",
                "content": response
            })

        # 👇 DEPOIS: decide o que mostrar no topo
        if len(st.session_state.messages) == 0:
            self.head()
        else:
            st.button("Reset Chat", on_click=self._reset_chat)

        # 👇 Renderiza histórico
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

    def run(self):
        self.page()

if __name__ == "__main__":
    page = Idle()
    page.run()

# streamlit run chat.py
# streamlit run src/web_applications/applications/idle.py