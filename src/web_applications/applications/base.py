import streamlit as st

class BaseApplication:
    def __init__(self):
        pass

    def app(self):
        st.title("BetterAI — Base Page")
        st.write("### Where Intelligence Finds Purpose")

    def run(self):
        self.app()

if __name__ == "__main__":
    page = BaseApplication()
    page.run()

# streamlit run src/web_applications/applications/base.py