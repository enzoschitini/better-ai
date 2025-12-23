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
            operation["embedding_cost"]["total_cost"]["cost_usd"]
        )

        has_usd_credit = (budget_usd - used_usd) >= operation_usd

        # ===== TOKENS =====
        budget_tokens = self.plan["resorce"]["tokens"]["monthly_budget_total_tokens"]
        used_tokens = self.plan["tokens"]["total_tokens"]
        operation_tokens = operation["embedding_cost"]["tokens"]

        has_token_credit = (budget_tokens - used_tokens) >= operation_tokens

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
        operation_usd = Decimal(
            operation["embedding_cost"]["total_cost"]["cost_usd"]
        )
        operation_tokens = int(operation["embedding_cost"]["tokens"])

        # ===== ATUALIZA CUSTO (USD) =====
        self.plan["cost"]["input_cost_usd"] = str(
            Decimal(self.plan["cost"]["input_cost_usd"]) + operation_usd
        )
        self.plan["cost"]["total_cost_usd"] = str(
            Decimal(self.plan["cost"]["total_cost_usd"]) + operation_usd
        )

        # ===== ATUALIZA TOKENS =====
        self.plan["tokens"]["input_tokens"] += operation_tokens
        self.plan["tokens"]["total_tokens"] += operation_tokens

        return self.plan


