from importlib import import_module


class GetPromptStyle:
    _BASE_STYLE_MODULE = "src.web_applications.pages.acquarello.stiles"
    _TASK_TO_ATTRIBUTE = {
        "text_to_image": "TEXT_TO_IMAGE_INSTRUCTIONS",
        "image_to_image": "IMAGE_TO_IMAGE_INSTRUCTIONS",
    }

    def __init__(self, style: str):
        self.style = (style or "").strip().lower()

        if not self.style:
            raise ValueError("`style` is required.")

    def _load_style_module(self):
        try:
            return import_module(f"{self._BASE_STYLE_MODULE}.{self.style}")
        except Exception as e:
            raise ValueError(f"Unsupported style '{self.style}': {str(e)}") from e

    def _get_task_prompt(self, task: str) -> str:
        attr_name = self._TASK_TO_ATTRIBUTE.get(task)

        if not attr_name:
            raise ValueError(f"Unsupported task '{task}'.")

        module = self._load_style_module()

        try:
            return getattr(module, attr_name)
        except Exception as e:
            raise ValueError(
                f"Style '{self.style}' does not define '{attr_name}': {str(e)}"
            ) from e

    def text_to_image(self) -> str:
        return self._get_task_prompt("text_to_image")

    def image_to_image(self) -> str:
        return self._get_task_prompt("image_to_image")


# Backward compatibility for existing imports.
GetPromptStile = GetPromptStyle