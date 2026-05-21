from fastapi import APIRouter, Depends, HTTPException, Form, File, UploadFile
from typing import Optional, List
from pydantic import BaseModel

from src.web_services_network.utils.request_resource import RequestResorse, Authorization

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

