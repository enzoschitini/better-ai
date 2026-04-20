import streamlit as st

st.set_page_config(page_title="BetterAI", page_icon="AI")
st.image("images/Frame 27346.png")

with st.sidebar:
    context = st.selectbox(
        label="",
        options=["Applications", "Documentation"],
    )

    if context == "Applications":
        st.write("Applications")

    elif context == "Documentation":
        st.write("Documentation")

# streamlit run src/web_applications/app.py