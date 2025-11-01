class PlanStatusVerifier:
    """Verifica se o uso do plano ultrapassou os limites."""

    @staticmethod
    def verify(plan_data: dict) -> str:
        try:
            plan = plan_data["plan"]
            resource_tokens = plan["resorce"]["tokens"]
            resource_costs = plan["resorce"]["cost"]
            used_tokens = plan["tokens"]
            used_costs = plan["cost"]

            if (used_tokens["input_tokens"] > resource_tokens["monthly_budget_input_tokens"] or
                used_tokens["output_tokens"] > resource_tokens["monthly_budget_output_tokens"] or
                used_tokens["total_tokens"] > resource_tokens["monthly_budget_total_tokens"]):
                return "no_activated"

            if (float(used_costs["input_cost_usd"]) > float(resource_costs["monthly_budget_input_cost_usd"]) or
                float(used_costs["output_cost_usd"]) > float(resource_costs["monthly_budget_output_cost_usd"]) or
                float(used_costs["total_cost_usd"]) > float(resource_costs["monthly_budget_total_cost_usd"])):
                return "no_activated"

            return "activated"

        except KeyError as e:
            raise ValueError(f"Campo ausente no JSON: {e}")
