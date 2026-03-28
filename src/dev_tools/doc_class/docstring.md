```python
from src.image_generation.cost_calculator.pricing_table import PricingTable
from typing import List, Dict


class CostCalculator:
    """
    Responsável por calcular custos baseados em diferentes métricas de token e imagens, 
    utilizando uma tabela de preços fornecida para realizar os cálculos.

    Args:
        pricing_table (PricingTable): Uma tabela de preços para cálculo dos custos. Default é PricingTable.

    Methods:
            merge_cost_information(cost_infos): Combina várias informações de custo em um único dicionário com totais consolidados.
            calculate(model, prompt_tokens, output_tokens, total_tokens, num_images, cached_prompt_tokens, cache_storage_tokens, cache_storage_hours): Calcula o custo total baseado na quantidade de tokens e imagens, considerando caching e armazenamento.
    """

    def __init__(self, pricing_table: PricingTable = PricingTable):
        self.pricing_table = pricing_table

    def merge_cost_information(self, cost_infos: List[Dict]) -> Dict:
        """
        Combina múltiplos dicionários de informações de custo em um único dicionário, somando os valores de tokens.

        Args: 
        cost_infos (List[Dict]): Uma lista de dicionários contendo informações de tokens para prompt, saída e total.

        Returns:
                Dict: Um dicionário com os totais somados de prompt_tokens, output_tokens e total_tokens.

        Raises:
                ValueError: Se a lista cost_infos contiver menos de dois elementos.
        """
        if not cost_infos or len(cost_infos) < 2:
            raise ValueError("You must provide at least two cost_information objects.")

        merged = {
            "prompt_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
        }

        for cost in cost_infos:
            merged["prompt_tokens"] += cost.get("prompt_tokens", 0)
            merged["output_tokens"] += cost.get("output_tokens", 0)
            merged["total_tokens"] += cost.get("total_tokens", 0)

        return merged

    def calculate(
        self,
        model: str,
        prompt_tokens: int,
        output_tokens: int,
        total_tokens: int,
        num_images: int = 0,
        cached_prompt_tokens: int = 0,
        cache_storage_tokens: int = 0,
        cache_storage_hours: float = 0.0,
    ) -> Dict[str, float]:
        """
        Calcula o custo total baseado no modelo, quantidade de tokens de prompt, saída, total, imagens geradas, e custos relacionados ao cache.

        Args: 
        model (str): Nome do modelo utilizado para buscar preços.
        prompt_tokens (int): Quantidade de tokens no prompt.
        output_tokens (int): Quantidade de tokens na saída gerada.
        total_tokens (int): Total de tokens envolvidos.
        num_images (int, optional): Quantidade de imagens geradas. Default é 0.
        cached_prompt_tokens (int, optional): Quantidade de tokens de prompt armazenados em cache. Default é 0.
        cache_storage_tokens (int, optional): Quantidade de tokens armazenados em cache para custeio. Default é 0.
        cache_storage_hours (float, optional): Horas que os tokens estão armazenados no cache. Default é 0.0.

        Returns:
                Dict[str, float]: Um dicionário contendo tokens e seus respectivos custos em dólares, arredondados para seis casas decimais.
        """
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
            "prompt_tokens": prompt_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "prompt_usd": round(prompt_cost, 6),
            "output_usd": round(output_cost, 6),
            "images_usd": round(image_cost, 6),
            "total_usd": round(total_cost, 6),
        }
```