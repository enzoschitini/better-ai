import json
import yaml
import logging
from pydantic import BaseModel, Field

from langchain_openai import ChatOpenAI
from langchain.output_parsers import PydanticOutputParser
from langchain.prompts import PromptTemplate

from dotenv import load_dotenv
import os

load_dotenv()


class PromptLoader:
    def __init__(self, path: str):
        with open(path, "r", encoding="utf-8") as file:
            self.data = yaml.safe_load(file) or {}

    def get(self, key: str, **variables):
        value = self.data
        for k in key.split("."):
            value = value[k]

        return value.format(**variables) if isinstance(value, str) else value




loader = PromptLoader("src/text_classifier.template_base/prompt.yaml")
transcription = "transcriptiontranscriptiontranscriptiontranscriptiontranscriptiontranscription"

prompt = loader.get(
    "parse_prompt",
    transcription=transcription
)

print(prompt)

schema = loader.get("resumo_do_video")

title = loader.get("resumo_do_video.title")
description = loader.get("resumo_do_video.description")
examples = loader.get("resumo_do_video.examples")

print(prompt)
print(schema)
print(title)
print(description)
print(examples)
