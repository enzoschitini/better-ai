import streamlit as st

st.set_page_config(page_title="Mini Chat Fake", page_icon="💬")

st.title("💬 Mini Chat IA (Simulado)")

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
    response = get_fake_response(prompt)

    # Salva resposta
    st.session_state.messages.append({
        "role": "assistant",
        "content": response
    })

    # Mostra resposta
    with st.chat_message("assistant"):
        st.markdown(response)

# streamlit run src/web_applications/applications/chat.py