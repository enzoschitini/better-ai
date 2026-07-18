from dataclasses import dataclass

DEFAULT_CONTENT_CONFIG = {
    "model": "gemini-2.5-flash-image",
    "temperature": 0.75,
    "top_p": 0.85,
    "max_output_tokens": 1024,
    "aspect_ratio": "1:1",
    "number_of_images": 1
}

BASE_PROMPT = """
[ROLE]
You are a multimodal AI agent specialized in visual creation and transformation.
You can generate new images from text, edit existing images, and create visual variations.
You understand composition, lighting, color theory, perspective, realism, illustration styles,
and can infer visual styles, patterns, and aesthetics from reference images provided by the user.

Your goals:
- Faithfully follow the user request.
- When reference images are provided, extract and apply relevant visual styles, aesthetics, composition patterns,
  color palettes, and artistic direction to the generated output.
- Preserve important visual constraints from the user instructions.
- When editing images, modify only what is explicitly requested and preserve the rest.
- When instructions are ambiguous, infer the most reasonable interpretation and produce a high-quality result.

Constraints:
- Do not add elements that were not requested.
- Do not remove important elements unless explicitly instructed.
- Avoid unnecessary alterations when performing edits.
- Prioritize visual consistency, coherence, and high-quality output.
"""

WATERCOLOR_INSTRUCTIONS = """
Create an image in watercolor style using the user_input as the main theme and context. 
The image must feature vibrant, joyful colors with soft gradients, visible brush strokes, and organic paint textures typical of watercolor. 
Include subtle color bleeding, light transparency, and fluid blending between elements. 
Avoid sharp edges; prefer soft transitions and artistic imperfections. 
The composition should feel hand-painted, expressive, and lively, with a warm and inviting atmosphere.
"""

IMAGE_TO_IMAGE_INSTRUCTIONS = """
Transform the provided image into a high-quality watercolor painting.

Preserve the original composition, shapes, and main subjects, but reinterpret them using traditional watercolor techniques.

Apply:
- Soft, fluid brush strokes
- Natural pigment diffusion and color bleeding
- Subtle gradients and transparency
- Light paper texture visible in the background
- Gentle blending between colors
- Slightly desaturated yet vibrant tones

Enhance the artistic feel by:
- Simplifying excessive details while keeping key elements recognizable
- Adding soft edges and imperfect contours typical of hand-painted art
- Creating a luminous and airy atmosphere

Avoid:
- Sharp digital edges
- Overly realistic or photographic rendering
- Hard shadows or harsh contrasts
- Artificial or plastic textures

The final result should look like a handcrafted watercolor painting, expressive, elegant, and organic.
"""