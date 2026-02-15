import magic
import os

from google.genai import types

from src.image_generation.utils.config import DEFAULT_CONTENT_CONFIG, BASE_PROMPT
from src.image_generation.utils.gemini_client import GeminiClient

from typing import List, Dict, Optional
from dotenv import load_dotenv

load_dotenv()

class ImageGeneratorService:
    """
    Serviço responsável por orquestrar todo o fluxo de geração e edição de imagens com o Gemini: 
    
    1. Construção do prompt multimodal (texto + imagens)
    2. Configuração de parâmetros de geração
    3. Chamadas ao modelo
    4. Parse das respostas (imagens, texto e métricas de uso).
    """
    def __init__(self, client=None, content_config: Optional[Dict] = None):
        """
        Inicializa o serviço de geração de imagens com o client do Gemini e as configurações de conteúdo.

        :param self: Instância do serviço.
        :param client: Client do Gemini já inicializado. Se None, um novo client é criado automaticamente.
        :type client: Optional[genai.Client]
        :param content_config: Configurações customizadas de geração (modelo, temperature, top_p,
                              aspect_ratio, number_of_images, etc).
        :type content_config: Optional[Dict]

        :raises TypeError: Caso o client fornecido não possua o atributo `.models`.
        :note: O client deve ser uma instância válida do SDK do Gemini. Não passe dicionários ou configs brutas.
        """
        try:
            self.client = client or GeminiClient().get_client()
            self.DEFAULT_CONTENT_CONFIG = DEFAULT_CONTENT_CONFIG
            self.content_config = self._build_content_config(content_config)
        except Exception as e:
            raise RuntimeError(f"Error initializing ImageGeneratorService: {str(e)}") from e

    def _build_content_config(self, content_config: Optional[Dict]) -> Dict:
        """
        Mescla as configurações padrão com as configurações customizadas fornecidas pelo usuário.

        :param self: Instância do serviço.
        :param content_config: Dicionário opcional com sobrescrita de configurações padrão.
        :type content_config: Optional[Dict]

        :return: Dicionário final de configuração de geração.
        :rtype: Dict

        :note: Valores ausentes em `content_config` herdam automaticamente os valores de DEFAULT_CONTENT_CONFIG.
        """
        
        return {
            **self.DEFAULT_CONTENT_CONFIG,
            **(content_config or {})
        }

    def _build_text_input_metadata(
        self,
        user_prompt: str,
        instructions: Optional[str],
        images: Optional[List[bytes]]
    ) -> Dict:
        """
        :param user_prompt: Prompt do usuário.
        :param instructions: Instruções adicionais (opcional).
        :param images: Imagens de entrada em bytes (opcional).
        :return: Dicionário com prompt, instruções e quantidade de imagens.
        """
        return {
            "user_prompt": user_prompt,
            "instructions": instructions,
            "images_count": len(images) if images else 0
        }


    # 1. Build Parts (Prompt + Imagens)
    def build_parts(self, user_prompt: str, instructions: Optional[str] = None, images: Optional[List[bytes]] = None) -> List[types.Part]:
        """
        Constrói as partes multimodais da requisição para o Gemini (texto + imagens de referência).

        :param self: Instância do serviço.
        :param prompt: Texto principal descrevendo a imagem a ser gerada ou editada.
        :type prompt: str
        :param instructions: Instruções adicionais de contexto ou regras de geração (opcional).
        :type instructions: Optional[str]
        :param images: Lista de imagens em bytes usadas como referência para edição ou variação.
        :type images: Optional[List[bytes]]

        :return: Lista de partes formatadas para envio ao Gemini.
        :rtype: List[types.Part]

        :raises ValueError: Caso o prompt seja vazio ou não seja uma string válida.
        :note: Quando imagens são fornecidas, o Gemini tende a interpretar a tarefa como edição/variação da imagem.
        """
        try:
            if not user_prompt or not isinstance(user_prompt, str):
                raise ValueError("`user_prompt` é obrigatório.")

            self.text_input = self._build_text_input_metadata(
                user_prompt=user_prompt,
                instructions=instructions,
                images=images
            )

            prompt = f"""
            {BASE_PROMPT}

            [TASK]
            {user_prompt}
            """

            if instructions:
                prompt += f"""

            [USER_CONTEXT]
            {instructions}
            """

            parts = [
                types.Part.from_text(text=prompt)
            ]

            if images:
                mime = magic.Magic(mime=True)

                for image_bytes in images:
                    mime_type = mime.from_buffer(image_bytes)

                    parts.append(
                        types.Part.from_bytes(
                            data=image_bytes,
                            mime_type=mime_type
                        )
                    )

            return parts
        except Exception as e:
            raise RuntimeError(f"Error building parts for model: {str(e)}") from e
    
    # 2. Config (temperature, top_p, max_tokens, etc)
    def generate_config(self):
        """
        Cria o objeto de configuração da geração para o Gemini.

        :param self: Instância do serviço.

        :return: Objeto de configuração de geração do Gemini.
        :rtype: types.GenerateContentConfig

        :note: O SDK atual do Gemini não permite configurar o número de imagens por chamada.
               A geração de múltiplas imagens é feita via múltiplas chamadas ao modelo.
        """
        try:
            config = types.GenerateContentConfig(
                temperature=self.content_config["temperature"],
                top_p=self.content_config["top_p"],
                max_output_tokens=self.content_config["max_output_tokens"],
                response_modalities=["IMAGE", "TEXT"],
                image_config=types.ImageConfig(
                    aspect_ratio=self.content_config["aspect_ratio"]
                )
            )

            return config
        except Exception as e:
            raise RuntimeError(f"Error building generation config: {str(e)}") from e
    
    # 3. Model Call
    def call_model(self, parts: List[Dict], config: Dict):
        """
        Executa múltiplas chamadas ao modelo de geração de imagens do Gemini com o mesmo prompt,
        gerando variações independentes da imagem.

        :param self: Instância do serviço.
        :param parts: Lista de partes multimodais (texto + imagens) para envio ao modelo.
        :type parts: List[Dict]
        :param config: Configuração de geração do Gemini.
        :type config: Dict

        :return: Lista de respostas retornadas pelo Gemini (uma por imagem gerada).
        :rtype: List[Any]

        :raises RuntimeError: Pode ser propagado em caso de falhas na API do Gemini.
        :note: O número de chamadas é controlado por `content_config["number_of_images"]`.
               Evite valores altos para não exceder rate limits ou custos.
        """
        try:
            contents = [
                types.Content(
                    role="user",
                    parts=parts
                )
            ]

            responses = []

            for _ in range(self.content_config["number_of_images"]):
                response = self.client.models.generate_content(
                    model=self.content_config["model"],
                    contents=contents,
                    config=config
                )
                responses.append(response)

            return responses
        except Exception as e:
            raise RuntimeError(f"Error calling image generation model: {str(e)}") from e

    
    # 4. Response Parse (múltiplos responses → text + imagens + metadados agregados)
    def parse_responses(self, responses):
        """
        Processa e agrega múltiplas respostas retornadas pelo Gemini, extraindo imagens,
        textos auxiliares e métricas de uso de tokens.

        :param self: Instância do serviço.
        :param responses: Lista de responses retornados pelo Gemini.
        :type responses: List[Any]

        :return: Estrutura agregada contendo imagens, textos e metadados de uso.
        :rtype: Dict[str, Any]

        :note: Cada response pode conter múltiplas partes (imagem e texto).
               O método agrega todas as imagens em uma única lista.
        """
        try:
            images = []
            usage_metadatas = []
            text_responses = []

            for response in responses:
                # Coleta imagens
                if response.candidates:
                    for part in response.candidates[0].content.parts:
                        if part.inline_data:
                            images.append({
                                "mime_type": part.inline_data.mime_type,
                                "data": part.inline_data.data  # bytes puros
                            })
                        elif part.text:
                            text_responses.append(part.text)

                # Coleta usage metadata por response
                if response.usage_metadata:
                    usage_metadatas.append({
                        "prompt_tokens": response.usage_metadata.prompt_token_count,
                        "output_tokens": response.usage_metadata.candidates_token_count,
                        "total_tokens": response.usage_metadata.total_token_count
                    })
                else:
                    usage_metadatas.append(None)

            return {
                **({"text_input": self.text_input} if getattr(self, "text_input", None) else {}), # Input textual do usuário
                "text_responses": text_responses, # Lista de respostas textuais
                "images": images, # Imagens de todos os responses
                "generate_config": self.content_config, # Config geral
                "usage_metadata": usage_metadatas, # Usage por responses
            }
        
        except Exception as e:
            raise RuntimeError(f"Error parsing model responses: {str(e)}") from e


















if __name__ == "__main__":

    import os
    import uuid

    # Load images

    base_image_paths = [
        "src/image_generation/backup/img1.jpeg",
        "src/image_generation/backup/img2.jpeg"
    ]

    images = []

    for path in base_image_paths:
        with open(path, "rb") as f:
            image_bytes = f.read()
        
        images.append(image_bytes)

    editor = ImageGeneratorService(content_config={"number_of_images": 2})
    
    parts = editor.build_parts(
        user_prompt="Gere uma imagem seguindo o estilo dessas",
        instructions="Crie uma imagem que combine elementos de ambas as imagens fornecidas, mantendo um estilo artístico coeso e atraente.",
        images=images
    )
    
    config = editor.generate_config()
    response = editor.call_model(parts, config)
    responses_parsed = editor.parse_responses(response)

    print("Text Input:", responses_parsed["text_input"])
    print("Text Responses:", responses_parsed["text_responses"])
    print("Usage Metadata:", responses_parsed["usage_metadata"])
    print("Config:", responses_parsed["generate_config"])

    os.makedirs("img_test", exist_ok=True)

    for i, image in enumerate(responses_parsed["images"]):
        ext = image["mime_type"].split("/")[-1]  # png, jpeg, webp, etc
        filename = f"img_test/img_{i}_{uuid.uuid4().hex}.{ext}"

        with open(filename, "wb") as f:
            f.write(image["data"])

        print("Imagem salva em:", filename)




ImageEditPayload = {
    "prompt": "Gere uma imagem seguindo o estilo dessas",

    "content_config": {
        "model": "gemini-2.5-flash-image",
        "temperature": 0.75,
        "top_p": 0.85,
        "max_output_tokens": 1024,
        "aspect_ratio": "9:16"
    },

    "images": [
        {
            "bytes": b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00...\xff...",
            "mime_type": "image/jpeg"
        },
        {
            "bytes": b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00...\xff...",
            "mime_type": "image/jpeg"
        }
    ]
}

ImageEditResponse = {
    "text_response": "Claro, aqui está a imagem solicitada.",

    "images": [
        {
            "bytes": b"\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x00\x00...\xff...",
            "mime_type": "image/jpeg"
        }
    ],

    "usage_metadata": {
        "prompt_tokens": 100,
        "output_tokens": 100,
        "total_tokens": 200
    }
}


# python -m src.image_generation.edit






