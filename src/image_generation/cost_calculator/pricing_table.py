from dataclasses import dataclass
from typing import Optional, Dict


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
