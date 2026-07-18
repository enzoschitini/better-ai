
class GetPromptStile:
    def __init__(self, stile: str):
        self.stile = stile

    def text_to_image(self) -> str:
        if self.stile == "watercolor":
            from src.web_applications.pages.acquarello.stiles.watercolor import TEXT_TO_IMAGE_INSTRUCTIONS
            return TEXT_TO_IMAGE_INSTRUCTIONS
        else:
            raise ValueError(f"Stile '{self.stile}' não suportado para text_to_image.")

    def image_to_image(self) -> str:
        if self.stile == "watercolor":
            from src.web_applications.pages.acquarello.stiles.watercolor import IMAGE_TO_IMAGE_INSTRUCTIONS
            return IMAGE_TO_IMAGE_INSTRUCTIONS
        else:
            raise ValueError(f"Stile '{self.stile}' não suportado para image_to_image.")