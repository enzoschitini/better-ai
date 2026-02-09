from dataclasses import dataclass

@dataclass
class GeneratedImage:
    image_bytes: bytes
    mime_type: str