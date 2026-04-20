import importlib
import streamlit as st

from src.web_applications.config import PAGES

st.set_page_config(page_title="BetterAI", page_icon="AI")

# Estado inicial
if "page" not in st.session_state:
    st.session_state.page = None

with st.sidebar:
    context = st.selectbox(
        "",
        PAGES.keys(),
        label_visibility="collapsed"
    )

    for page in PAGES[context]:
        if st.button(page, use_container_width=True):
            st.session_state.page = page

if st.session_state.page is None:
    st.session_state.page = PAGES[context][0]

page_name = st.session_state.page.lower()  # ex: "Home" → "home"
module_path = f"src.web_applications.applications.{page_name}"

module = importlib.import_module(module_path)
page_class = getattr(module, st.session_state.page)

page = page_class()
page.run()

# streamlit run webapp.py