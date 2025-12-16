import json
from src.chat.utils.mongo_manage import MongoDBManager

mongo = MongoDBManager()

business = mongo.buscar_documentos(database_name="TokensUsage",
                                   collection_name="BusinessAccountManage", 
                                   filtro={"business_id": "0011"})[0]

embedding_cost = { 
    "embedding_cost": {
        "embedding_model": "text-embedding-3-large",
        "model_cost_per_1000_tokens": "0.00013",
        "characters": 913,
        "tokens": 267,
        "total_cost": {
        "cost_usd": "0.00003471",
        "cost_eur": "0.0000295222",
        "cost_brl": "0.0001879998"
        },
        "dollar_rates": {
        "EUR": 0.85054,
        "BRL": 5.4163
        }
    }
  }

from decimal import Decimal


def has_credits_for_operation(plan_info: dict, operation_cost_info: dict) -> bool:
    """
    Retorna True se o plano tiver crédito suficiente
    TANTO em custo (USD) QUANTO em tokens.
    """

    # ==========
    # CUSTO (USD)
    # ==========

    monthly_budget_usd = Decimal(
        plan_info["resorce"]["cost"]["monthly_budget_total_cost_usd"]
    )

    used_cost_usd = Decimal(
        plan_info["cost"]["total_cost_usd"]
    )

    operation_cost_usd = Decimal(
        operation_cost_info["embedding_cost"]["total_cost"]["cost_usd"]
    )

    remaining_budget_usd = monthly_budget_usd - used_cost_usd

    has_cost_credit = remaining_budget_usd >= operation_cost_usd

    # ==========
    # TOKENS
    # ==========

    monthly_budget_tokens = int(
        plan_info["resorce"]["tokens"]["monthly_budget_total_tokens"]
    )

    used_tokens = int(
        plan_info["tokens"]["total_tokens"]
    )

    operation_tokens = int(
        operation_cost_info["embedding_cost"]["tokens"]
    )

    remaining_tokens = monthly_budget_tokens - used_tokens

    has_token_credit = remaining_tokens >= operation_tokens

    # ==========
    # REGRA FINAL (AND)
    # ==========

    return has_cost_credit and has_token_credit


print("\nInformações do plano da empresa (No banco)")
print(json.dumps(business["plan"], indent=4))
print("\nInformações do custo previsto para a operação")
print(json.dumps(embedding_cost, indent=4))

print(has_credits_for_operation(plan_info=business["plan"], operation_cost_info=embedding_cost))

# python -m src.embedding.test