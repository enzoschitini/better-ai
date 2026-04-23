import streamlit as st
#from src.web_applications.utils.render_components import Component

import streamlit as st
import base64

class Component:
    def __init__(self):
        pass

    def _get_base64_image(self, path):
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()
    
    def text(self, content, size=16, weight=400, align="left"):
        st.markdown(
            f"""
            <div style="text-align: {align}; font-size: {size}px; font-weight: {weight};">
                {content}
            </div>
            """,
            unsafe_allow_html=True
        )
    
    def image(self, path, width=None):
        img_base64 = self._get_base64_image(path)
        width_attr = f'width="{width}"' if width else ""
        st.markdown(
            f"""
            <div style="display: flex; justify-content: center;">
                <img src="data:image/png;base64,{img_base64}" {width_attr}>
            </div>
            """,
            unsafe_allow_html=True
        )


class Idle:
    def __init__(self):
        self.component = Component()

    def head(self):
        self.component.image("images/idle.png", width=150)
        st.write("")

        self.component.text("Agent Idle", size=50, weight=600, align="center")
        self.component.text("Ask your agent to do something!", size=30, align="center")
    
    def run(self):
        self.head()

if __name__ == "__main__":
    page = Idle()
    page.run()

# streamlit run src/web_applications/applications/idle.py