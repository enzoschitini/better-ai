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

def business_validation(plan: dict, operation: dict) -> bool:
    """
    Retorna True se o plano possuir créditos suficientes
    tanto em custo (USD) quanto em tokens.
    """

    # ===== CUSTO (USD) =====
    budget_usd = Decimal(plan["resorce"]["cost"]["monthly_budget_total_cost_usd"])
    used_usd = Decimal(plan["cost"]["total_cost_usd"])
    operation_usd = Decimal(operation["embedding_cost"]["total_cost"]["cost_usd"])

    has_usd_credit = (budget_usd - used_usd) >= operation_usd

    # ===== TOKENS =====
    budget_tokens = plan["resorce"]["tokens"]["monthly_budget_total_tokens"]
    used_tokens = plan["tokens"]["total_tokens"]
    operation_tokens = operation["embedding_cost"]["tokens"]

    has_token_credit = (budget_tokens - used_tokens) >= operation_tokens

    return has_usd_credit and has_token_credit


print("\nInformações do plano da empresa (No banco)")
print(json.dumps(business["plan"], indent=4))
print("\nInformações do custo previsto para a operação")
print(json.dumps(embedding_cost, indent=4))

print(
    business_validation(
        plan=business["plan"],
        operation=embedding_cost
    )
)

from decimal import Decimal
from copy import deepcopy


def business_update_usage(plan: dict, operation: dict) -> dict:
    """
    Atualiza o uso de créditos do plano (USD e tokens)
    com base no custo da operação de embedding.

    Retorna o plano atualizado.
    """

    if not business_validation(plan=plan, operation=operation):
        return "Créditos insuficientes para realizar a operação"

    # Trabalha com cópia para evitar side-effects
    updated_plan = deepcopy(plan)

    # ===== VALORES DA OPERAÇÃO =====
    operation_usd = Decimal(operation["embedding_cost"]["total_cost"]["cost_usd"])
    operation_tokens = int(operation["embedding_cost"]["tokens"])

    # ===== ATUALIZA CUSTO (USD) =====
    updated_plan["cost"]["input_cost_usd"] = str(
        Decimal(updated_plan["cost"]["input_cost_usd"]) + operation_usd
    )
    updated_plan["cost"]["total_cost_usd"] = str(
        Decimal(updated_plan["cost"]["total_cost_usd"]) + operation_usd
    )
    
    # ===== ATUALIZA TOKENS =====
    updated_plan["tokens"]["input_tokens"] += operation_tokens
    updated_plan["tokens"]["total_tokens"] += operation_tokens

    return updated_plan

print(json.dumps(business_update_usage(plan=business["plan"], operation=embedding_cost), indent=4))
# python -m src.embedding.test