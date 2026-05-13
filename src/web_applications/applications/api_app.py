import streamlit as st
import time

class ApiApp:
    def __init__(self):
        pass

    def head(self):
        st.title("API")
        st.write("Test")

        st.title("Demo - Status Box")

        if st.button("Start Process"):

            with st.status("Starting process...", expanded=True) as status:
                
                time.sleep(1)
                status.write("🔄 Loading data...")
                
                time.sleep(1)
                status.write("🧠 Processing...")
                
                time.sleep(1)
                status.write("🎨 Generating image...")
                
                time.sleep(1)

                status.update(
                    label="✅ Process completed!",
                    state="complete"
                )

    def run(self):
        self.head()
