from dataclasses import dataclass
from typing import Optional, Dict


# =========================
# Pricing Models
# =========================

@dataclass(frozen=True)
class ModelPricing:
    input_per_million_tokens: float
    output_per_million_tokens: float
    image_price_per_unit: Optional[float] = None
    cache_input_per_million_tokens: Optional[float] = None
    cache_storage_per_million_tokens_per_hour: Optional[float] = None


class PricingTable:
    VERSION = "2026-02-11"

    PRICES: Dict[str, ModelPricing] = {
        # =========================
        # Gemini 3
        # =========================
        "gemini-3-flash-preview": ModelPricing(
            input_per_million_tokens=0.50,
            output_per_million_tokens=3.00,
            image_price_per_unit=None,
            cache_input_per_million_tokens=0.05,
            cache_storage_per_million_tokens_per_hour=1.00,
        ),

        "gemini-3-pro-image-preview": ModelPricing(
            input_per_million_tokens=2.00,
            output_per_million_tokens=12.00,
            image_price_per_unit=0.134,  # 1K/2K (4K é $0.24 — se quiser eu adapto pra suportar resolução)
            cache_input_per_million_tokens=None,
            cache_storage_per_million_tokens_per_hour=None,
        ),

        # =========================
        # Gemini 2.5 Flash
        # =========================
        "gemini-2.5-flash": ModelPricing(
            input_per_million_tokens=0.30,
            output_per_million_tokens=2.50,
            image_price_per_unit=None,
            cache_input_per_million_tokens=0.03,
            cache_storage_per_million_tokens_per_hour=1.00,
        ),

        "gemini-2.5-flash-preview-09-2025": ModelPricing(
            input_per_million_tokens=0.30,
            output_per_million_tokens=2.50,
            image_price_per_unit=None,
            cache_input_per_million_tokens=0.03,
            cache_storage_per_million_tokens_per_hour=1.00,
        ),

        "gemini-2.5-flash-lite": ModelPricing(
            input_per_million_tokens=0.10,
            output_per_million_tokens=0.40,
            image_price_per_unit=None,
            cache_input_per_million_tokens=0.01,
            cache_storage_per_million_tokens_per_hour=1.00,
        ),

        "gemini-2.5-flash-lite-preview-09-2025": ModelPricing(
            input_per_million_tokens=0.10,
            output_per_million_tokens=0.40,
            image_price_per_unit=None,
            cache_input_per_million_tokens=0.01,
            cache_storage_per_million_tokens_per_hour=1.00,
        ),

        # =========================
        # Gemini Image Models
        # =========================
        "gemini-2.5-flash-image": ModelPricing(
            input_per_million_tokens=0.30,
            output_per_million_tokens=0.0,   # saída é imagem
            image_price_per_unit=0.039,
            cache_input_per_million_tokens=None,
            cache_storage_per_million_tokens_per_hour=None,
        ),

        # =========================
        # Gemini 2.0 Flash
        # =========================
        "gemini-2.0-flash": ModelPricing(
            input_per_million_tokens=0.10,
            output_per_million_tokens=0.40,
            image_price_per_unit=0.039,
            cache_input_per_million_tokens=0.025,
            cache_storage_per_million_tokens_per_hour=1.00,
        ),
    }

    @classmethod
    def get(cls, model: str) -> ModelPricing:
        if model not in cls.PRICES:
            raise ValueError(f"Modelo sem precificação cadastrada: {model}")
        return cls.PRICES[model]


# =========================
# Cost Calculator
# =========================

class CostCalculator:
    def __init__(self, pricing_table: PricingTable = PricingTable):
        self.pricing_table = pricing_table

    def calculate(
        self,
        model: str,
        prompt_tokens: int,
        output_tokens: int,
        num_images: int = 0,
        cached_prompt_tokens: int = 0,
        cache_storage_tokens: int = 0,
        cache_storage_hours: float = 0.0,
    ) -> Dict[str, float]:
        pricing = self.pricing_table.get(model)

        # Tokens cost
        prompt_cost = (prompt_tokens / 1_000_000) * pricing.input_per_million_tokens

        output_cost = 0.0
        if pricing.output_per_million_tokens and output_tokens:
            output_cost = (output_tokens / 1_000_000) * pricing.output_per_million_tokens

        # Image cost
        image_cost = 0.0
        if pricing.image_price_per_unit and num_images:
            image_cost = num_images * pricing.image_price_per_unit

        # Cache input cost
        cache_input_cost = 0.0
        if pricing.cache_input_per_million_tokens and cached_prompt_tokens:
            cache_input_cost = (
                cached_prompt_tokens / 1_000_000
            ) * pricing.cache_input_per_million_tokens

        # Cache storage cost
        cache_storage_cost = 0.0
        if (
            pricing.cache_storage_per_million_tokens_per_hour
            and cache_storage_tokens
            and cache_storage_hours
        ):
            cache_storage_cost = (
                cache_storage_tokens / 1_000_000
            ) * pricing.cache_storage_per_million_tokens_per_hour * cache_storage_hours

        total_cost = (
            prompt_cost
            + output_cost
            + image_cost
            + cache_input_cost
            + cache_storage_cost
        )

        return {
            "model": model,
            "pricing_version": self.pricing_table.VERSION,
            "prompt_tokens": prompt_tokens,
            "output_tokens": output_tokens,
            "num_images": num_images,
            "prompt_usd": round(prompt_cost, 6),
            "output_usd": round(output_cost, 6),
            "images_usd": round(image_cost, 6),
            "cache_input_usd": round(cache_input_cost, 6),
            "cache_storage_usd": round(cache_storage_cost, 6),
            "total_usd": round(total_cost, 6),
        }

import json

calculator = CostCalculator()

usage = {
    "prompt_tokens": 526,
    "output_tokens": 12,
}

cost = calculator.calculate(
    model="gemini-3-pro-image-preview",
    prompt_tokens=usage["prompt_tokens"],
    output_tokens=usage["output_tokens"],
    num_images=1,
)

print(json.dumps(cost, indent=4))

# https://ai.google.dev/gemini-api/docs/pricing?utm_source=chatgpt.com&hl=it

BEST_TO_WORST_MODELS = [
    "gemini-3-pro-image-preview",
    "gemini-3-flash-preview",
    "gemini-2.5-flash",
    "gemini-2.5-flash-preview-09-2025",
    "gemini-2.5-flash-image",
    "gemini-2.0-flash",
    "gemini-2.5-flash-lite-preview-09-2025",
    "gemini-2.5-flash-lite",
]
