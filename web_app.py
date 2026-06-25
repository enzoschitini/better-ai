import streamlit as st
from src.web_applications.utils.pages import PAGES

st.set_page_config(
    page_title="BetterAI",
    page_icon="✦",
    layout="wide",
)

navigation = st.navigation(list(PAGES.values()), position="hidden")
navigation.run()

# streamlit run web_app.py