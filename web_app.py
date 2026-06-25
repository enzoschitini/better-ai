import streamlit as st
from pages import PAGES

# ---------------------------------------------------------------------------
# Entry point — apenas configura e roda a navegação
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="BetterAI",
    page_icon="✦",
    layout="wide",
)

navigation = st.navigation(list(PAGES.values()), position="hidden")
navigation.run()

# streamlit run web_app.py

# streamlit run web_app.py