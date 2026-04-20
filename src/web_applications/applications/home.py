import streamlit as st

class Home:
    def __init__(self):
        pass

    def head(self):
        st.image("images/Frame 27346.png")

        st.title("Home")
        st.write("Test")
    
    def run(self):
        self.head()
