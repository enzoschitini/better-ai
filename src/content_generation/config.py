from typing import List, Optional
from pydantic import BaseModel, Field

class GeneratedContentParse(BaseModel):
    title: str = Field(..., description="Main title for the generated content")
    summary: str = Field(..., description="Short summary with 1-2 sentences")
    body: str = Field(..., description="Main content text")
    cta: str = Field(..., description="Call to action")
    hashtags: List[str] = Field(
        ..., description="Relevant social hashtags, each item must start with #"
    )
    sources_used: List[str] = Field(
        ..., description="List of key source snippets or documents used"
    )
    product_mentions: List[str] = Field(
        ..., description="List of any specific products mentioned in the content"
    )
    pricing_info: Optional[str] = Field(
        None, description="Any pricing information included in the content, if applicable"
    )


class ContentBatchOutput(BaseModel):
    query: str
    objective: str
    content_count: int
    items: List[GeneratedContentParse]
    relevant_docs: List[dict]
    usage_metadata: Optional[dict] = None
    latency: Optional[float] = None

MODEL_PROVIDER_MAP = {
    "gpt-4.1-mini": "openai",

    "claude-opus-4-5": "anthropic",
    "claude-sonnet-4-6": "anthropic",

    "gemini-2.5-pro": "google",

    "llama-3.3-70b-versatile": "groq",
}

DEFAULT_MODEL = "gpt-4.1-mini"
DEFAULT_MAX_RESULTS = 5
DEFAULT_CONTENT_COUNT = 1
DEFAULT_BODY_MIN_CHARS = 700
DEFAULT_BODY_MAX_CHARS = 1200

PINECONE_INDEX_NAME = "backai-vectorstore"
PINECONE_MAIN_NAMESPACE = "knowledge_base_content_agent_oboticario"

AGENT_INSTRUCTIONS = [
    "You are a content creation specialist.",
    "Always use only the provided context as the primary source.",
    "If context is insufficient, state what is missing instead of inventing facts.",
    "Return polished, coherent, publication-ready content.",
    "The output must strictly follow the requested structured fields.",
    "Generate relevant hashtags aligned with the topic and objective.",
]

AGENT_DESCRIPTION = "Generates content using retrieval context as input."

VARIATION_ANGLES = [
    "benefit-driven narrative",
    "practical educational approach",
    "premium positioning perspective",
    "problem-solution framing",
    "light comparative framing",
]

VARIATION_OPENINGS = [
    "Start with a concise insight statement.",
    "Start with a short practical scenario.",
    "Start with a premium brand-oriented hook.",
    "Start with a common pain point.",
    "Start with a contrast between options.",
]

VARIATION_RHYTHMS = [
    "Use medium paragraphs.",
    "Use shorter paragraphs and faster pacing.",
    "Use a more refined and descriptive pacing.",
    "Use direct and objective pacing.",
    "Use balanced pacing with one concise list if useful.",
]

PROMPT_BASE_TEMPLATE = """
Objective:
{objective}

User query for retrieval:
{query}

Retrieved context:
{context}

Additional requirements:
{extra_requirements}

Variant:
{variant_number} of {content_count}

Instructions:
- Build the final content grounded in the retrieved context.
- Keep a clear structure and avoid unsupported facts.
- Make this variant distinct in angle and wording from the others.
- Preferred angle for this variant: {variation_angle}.
- Opening guidance: {variation_opening}
- Writing rhythm guidance: {variation_rhythm}
- The body field must have between {body_min_chars} and {body_max_chars} characters.
- Include 5 to 10 relevant hashtags in the hashtags field.
""".strip()

PROMPT_CORRECTION_TEMPLATE = """
{prompt_base}

Correction:
- Previous body length was {previous_body_length} characters.
- Regenerate and strictly keep body length between {body_min_chars} and {body_max_chars}.
""".strip()

