import requests
import streamlit as st

#st.title("Teste de CURL Compiler")
result = requests.post(
    "http://localhost:8000/test-authorization",
    auth=("enzo", "senha123"),
    headers={
        "Authorization": "Bearer TOKEN_123",
    },
    json={"message": "Hello World"}
)