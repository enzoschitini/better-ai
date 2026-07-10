from pathlib import Path

import streamlit as st
from src.web_applications.utils.pages import PAGES

FAVICON_PATH = Path(__file__).resolve().parent / "images" / "Logo.png"

st.set_page_config(
    page_title="BetterAI",
    page_icon=str(FAVICON_PATH),
    layout="wide",
)

navigation = st.navigation(list(PAGES.values()), position="hidden")
navigation.run()

# streamlit run web_app.py