import streamlit as st

from src.web_applications.config import PAGES
from src.web_applications.applications.home import Home

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

if st.session_state.page == "Home":
    page = Home()

page.run()

# streamlit run webapp.py