from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from typing import Optional, List
from pydantic import BaseModel

from src.web_services_network.request_resource import RequestResorse, Authorization

from src.image_generation.module import ImageGenerate, RequestProcessor

router = APIRouter(
    prefix="/davinci",
    tags=["image-generation"]
)

@router.post("/image-generation", 
    summary="Image generation based on prompts, settings, and optional images.",
    description="This endpoint accepts user input, optional instructions, configuration settings, and files to generate images using the ImageGenerate module. It processes the input and returns the generated images based on the provided parameters.",
    #dependencies=[Depends(Authorization.validate_api_key)]
)
async def image_generation(
    user_input: str = Form(..., title="User Input", description="Main prompt used to generate the image"),
    instructions: Optional[str] = Form(None, title="Instructions", description="Additional generation instructions or style guidance"),
    config: Optional[str] = Form(None, title="Config", description="Optional JSON configuration for image generation"),
    files: Optional[List[UploadFile]] = File(None, title="Reference Files", description="Optional reference images for generation"),
):
    try:
        resource = RequestResorse()

        processor = RequestProcessor(config=config, files=files)
        processor_result = await processor.process()

        config_dict = processor_result["config"]
        image_bytes = processor_result["image_bytes"]

        generator = ImageGenerate(
            user_input=user_input,
            instructions=instructions,
            config=config_dict,
            image_bytes=image_bytes
        )

        result = generator.runner()

        return resource.success_response(result)

    except Exception as e:
        return resource.error_response(e)

"""
curl --location "http://localhost:8000/davinci/image-generation" \
--header "Authorization: Bearer betterai-dev-96d97aa3-492d-4ecc-9ced-3dc34c0cf062-945d3391-85dc-4a19-a054-191d048b62c0" \
--header "Client: BETTERAI" \
--header "SecretKey: Bearer betterai-dev-6c6febc5-de97-464a-929b-cce1b2278de1" \
--form "user_input=Crea l'immagine di una pizzeria napoletana" \
--form "instructions=Lo stile deve essere un animazione 3d come quelle di disney" \
--form 'config={
  "model": "gemini-2.5-flash-image",
  "temperature": 0.75,
  "top_p": 0.85,
  "max_output_tokens": 1024,
  "aspect_ratio": "9:16",
  "number_of_images": 2
}' \
--form "files=@C:/Users/schit/Downloads/img_177124504231363320002Vw.jpg"
"""
