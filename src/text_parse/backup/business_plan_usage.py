from decimal import Decimal
from copy import deepcopy


# Classe separata:
class BusinessPlanUsage:
    """
    Responsável por validar e atualizar o uso de créditos
    (USD e tokens) de um plano de negócio.

usage = BusinessPlanUsage(plan)

if usage.validate(operation):
    updated_plan = usage.update_usage(operation)
    """

    def __init__(self, plan: dict):
        # Trabalha sempre com cópia para evitar side-effects
        self.plan = deepcopy(plan)

    # ======================================================
    # VALIDATION
    # ======================================================
    def validate(self, operation: dict) -> bool:
        """
        Retorna True se o plano possuir créditos suficientes
        tanto em custo (USD) quanto em tokens.
        """

        # ===== CUSTO (USD) =====
        budget_usd = Decimal(
            self.plan["resorce"]["cost"]["monthly_budget_total_cost_usd"]
        )

        used_usd = Decimal(self.plan["cost"]["total_cost_usd"])

        operation_usd = Decimal(
            operation["cost"]["usd"]["total_cost_usd"]
        )

        has_usd_credit = (budget_usd - used_usd) >= operation_usd

        # ===== TOKENS =====
        budget_tokens = self.plan["resorce"]["tokens"]["monthly_budget_total_tokens"]
        used_tokens = self.plan["tokens"]["total_tokens"]
        operation_tokens = operation["tokens"]["total_tokens"]

        has_token_credit = (budget_tokens - used_tokens) >= operation_tokens
        
        print(budget_tokens, used_tokens, operation_tokens)
        print(has_token_credit)

        return has_usd_credit and has_token_credit

    # ======================================================
    # UPDATE
    # ======================================================
    def update_usage(self, operation: dict, validate: bool = True) -> dict:
        """
        Atualiza o uso de créditos do plano (USD e tokens)
        com base no custo da operação de embedding.

        Retorna o plano atualizado.
        """

        #if validate and not self.validate(operation):
            #return "not_credits"

        # ===== VALORES DA OPERAÇÃO =====
        input_cost_usd = Decimal(
            operation["cost"]["usd"]["input_cost_usd"]
        )

        output_cost_usd = Decimal(
            operation["cost"]["usd"]["output_cost_usd"]
        )

        total_cost_usd = Decimal(
            operation["cost"]["usd"]["total_cost_usd"]
        )

        # ===== ATUALIZA CUSTO (USD) =====
        self.plan["cost"]["input_cost_usd"] = str(
            Decimal(self.plan["cost"]["input_cost_usd"]) + input_cost_usd
        )
        self.plan["cost"]["output_cost_usd"] = str(
            Decimal(self.plan["cost"]["output_cost_usd"]) + output_cost_usd
        )
        self.plan["cost"]["total_cost_usd"] = str(
            Decimal(self.plan["cost"]["total_cost_usd"]) + total_cost_usd
        )
        
        # ===== ATUALIZA TOKENS =====
        self.plan["tokens"]["input_tokens"] += int(operation["tokens"]["input_tokens"])
        self.plan["tokens"]["output_tokens"] += int(operation["tokens"]["output_tokens"])
        self.plan["tokens"]["total_tokens"] += int(operation["tokens"]["total_tokens"])

        return self.plan



from src.chat.utils.mongo_manage import MongoDBManager

operation = {
    "llm_model": {
        "name": "gpt-4o-mini",
        "input_cost_1k_usd": 0.00015,
        "output_cost_1k_usd": 0.0006
    },
    "tokens": {
        "input_tokens": 332,
        "output_tokens": 62,
        "total_tokens": 394
    },
    "cost": {
        "usd": {
            "input_cost_usd": "0.049800",
            "output_cost_usd": "0.037200",
            "total_cost_usd": "0.087000"
        },
        "eur": {
            "input_cost_eur": "0.042599",
            "output_cost_eur": "0.031821",
            "total_cost_eur": "0.074419"
        },
        "brl": {
            "input_cost_brl": "0.268761",
            "output_cost_brl": "0.200761",
            "total_cost_brl": "0.469522"
        }
    },
    "rates": {
        "EUR": 0.855396,
        "BRL": 5.396802
    }
}

mongo = MongoDBManager()
plan = mongo.buscar_documentos(database_name="TokensUsage", collection_name="BusinessAccountManage", filtro={"business_id": "0011"})[0]

updater = BusinessPlanUsage(plan["plan"])
new_plan = updater.update_usage(operation, True)

status = updater.validate(operation)

print("Status:", status)

if status == False:
    new_plan["status"] = "no_activated"

mongo.atualizar_documentos(
    database_name="TokensUsage",
    collection_name="BusinessAccountManage",
    filtro={"business_id": "0011"},
    novos_valores={"plan": new_plan}
)

print(new_plan)

# python -m src.text_parse.business_plan_usage