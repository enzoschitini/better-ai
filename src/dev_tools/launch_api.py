import json
import os
import uuid
import logging

from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Literal
from dotenv import load_dotenv

from fastapi import FastAPI, UploadFile, HTTPException, Request, Form, Body, Depends, Header, File
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware

class ASCII_API:
    def __init__(self):
        pass

    def standard(self):
        # 92m Verde
        # 97m Bianco

        logo = """
        \033[97m
        ╔═══════════════════════════════════════════════════════════════════════╗

            ██████╗ ███████╗████████╗████████╗███████╗██████╗      █████╗ ██╗ ✦
            ██╔══██╗██╔════╝╚══██╔══╝╚══██╔══╝██╔════╝██╔══██╗    ██╔══██╗██║
            ██████╔╝█████╗     ██║      ██║   █████╗  ██████╔╝    ███████║██║
            ██╔══██╗██╔══╝     ██║      ██║   ██╔══╝  ██╔══██╗    ██╔══██║██║
            ██████╔╝███████╗   ██║      ██║   ███████╗██║  ██║    ██║  ██║██║
            ╚═════╝ ╚══════╝   ╚═╝      ╚═╝   ╚══════╝╚═╝  ╚═╝    ╚═╝  ╚═╝╚═╝

        ╚═══════════════════════════════════════════════════════════════════════╝

                          ✦  Where intelligence finds purpose. ✦
        \033[0m
        """
        print(logo)



asci = ASCII_API()
asci.standard()

app = FastAPI()

@app.get("/healthy")
def healthy():
    return {"status": "ok"}

# uvicorn src.dev_tools.launch_api:app --reload 
# uvicorn app:app --reload  

# ------------------------------------------------- #
from src.utils.load_file.load_request_file import LoadRequestFile
from src.embedding.services.file_content_extractor import FileContentExtractor
from src.text_parse.content_parsing_agent import ContentParsingAgent

@app.post("/parse-content")
async def parse_content(
    schema: str = Form(...),
    file: UploadFile = File(...),
):
    try:

        loader = await LoadRequestFile(
            file=file,
            max_size_mb=5
        ).load()

        schema_data = json.loads(schema)

        file_bytes = loader.bytes
        raw_bytes = file_bytes.getvalue()
        file_extension = loader.extension

        print(type(file_bytes))  # BytesIO
        print(file_extension)    # extensão do arquivo
        print(len(raw_bytes))    # tamanho em bytes
        print(raw_bytes[:100])   # primeiros 100 bytes do arquivo

        extractor = FileContentExtractor(file_bytes, "pdf")
        result = extractor.extract()
        print(result["response"][:500])  # Imprime os primeiros 500 caracteres do conteúdo extraído

        agent_parser = ContentParsingAgent(
            input_data={
                "file_content": result["response"]
            },
            output_data={
                "summary": {
                    "type": "str",
                    "description": "Resumo do conteúdo do arquivo"
                }
            },
            #config_data=config_data
        )
        content_parsed = agent_parser.run_agent()
        response = agent_parser.format_response(content_parsed)

        return JSONResponse(content={
            "status": "success",
            "response": response
        })

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



