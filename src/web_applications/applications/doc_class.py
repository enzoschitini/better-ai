from pathlib import Path

import streamlit as st

from src.dev_tools.doc_class.module import ClassDoc
from src.web_applications.utils.pages import PAGES


def _sanitize_name(raw_name: str) -> str:
    sanitized = "".join(ch for ch in raw_name.strip() if ch.isalnum() or ch in ("-", "_"))
    return sanitized or "output"


st.markdown(
    """
    <style>
        [data-testid="stSidebarNav"] { display: none; }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("## 🧾 ClassDoc")
    st.markdown("---")
    st.markdown("Gerador de docstring e documentação em Markdown.")
    st.divider()
    st.page_link(PAGES["home"], label="← Voltar para Home")

st.title("ClassDoc")
st.caption("Insira o código Python e gere `docstring.md` e `documentation.md`.")
st.divider()

class_name = st.text_input("Nome da classe/pasta de saída", value="ModelGateway")
code_input = st.text_area(
    "Código Python para documentar",
    height=420,
    placeholder="Cole aqui a classe Python completa...",
)

col1, col2 = st.columns([1, 4])
generate_clicked = col1.button("Gerar", type="primary", use_container_width=True)
col2.caption("Os arquivos serão salvos em `src/dev_tools/doc_class/<nome>/`.")

if generate_clicked:
    if not code_input.strip():
        st.error("Insira o código Python antes de gerar a documentação.")
    else:
        safe_name = _sanitize_name(class_name)

        try:
            with st.spinner("Gerando documentação..."):
                runner = ClassDoc(class_name=safe_name)
                docstring_md, documentation_md, docstring_path, documentation_path = runner.generate_from_code(
                    code_input
                )

            st.success("Documentação gerada com sucesso.")

            st.markdown("### Arquivos gerados")
            st.write(f"- {Path(docstring_path).as_posix()}")
            st.write(f"- {Path(documentation_path).as_posix()}")

            dl_col1, dl_col2 = st.columns(2)
            dl_col1.download_button(
                label="Baixar docstring.md",
                data=docstring_md,
                file_name="docstring.md",
                mime="text/markdown",
                use_container_width=True,
            )
            dl_col2.download_button(
                label="Baixar documentation.md",
                data=documentation_md,
                file_name="documentation.md",
                mime="text/markdown",
                use_container_width=True,
            )

            tab_docstring, tab_documentation = st.tabs(["Docstring", "Documentation"])

            with tab_docstring:
                st.markdown(docstring_md)
                st.code(docstring_md, language="markdown")

            with tab_documentation:
                st.markdown(documentation_md)
                st.code(documentation_md, language="markdown")

        except Exception as exc:
            st.error(f"Erro ao gerar documentação: {exc}")