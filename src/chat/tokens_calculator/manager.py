from chat.tokens_calculator.cost_calculator import CostCalculator
from chat.tokens_calculator.plan_verifier import PlanStatusVerifier
from chat.tokens_calculator.repository import BusinessRepository

class BusinessPlanManager:
    """Orquestra o cálculo de custos e atualização de plano."""

    def __init__(self, business_id: str, model: str, tokens_data: dict, mongo):
        self.business_id = business_id
        self.model = model
        self.tokens_data = tokens_data
        self.repo = BusinessRepository(mongo)

    def execute(self):
        calculator = CostCalculator(self.model)
        updated_tokens = calculator.calculate(self.tokens_data)

        plan_data = self.repo.get_business_data(self.business_id)
        if not plan_data:
            raise ValueError(f"Empresa '{self.business_id}' não encontrada.")

        new_tokens = updated_tokens["cost"]

        for k in ["input_tokens", "output_tokens", "total_tokens"]:
            plan_data["plan"]["tokens"][k] += new_tokens[k]

        def format_decimal(value: float) -> str:
            return f"{value:.6f}"

        for k in ["input_cost_usd", "output_cost_usd", "total_cost_usd"]:
            plan_data["plan"]["cost"][k] = str(
                format_decimal(float(plan_data["plan"]["cost"][k]) + float(new_tokens[k]))
            )

        plan_status = PlanStatusVerifier.verify(plan_data)
        plan_data["plan"]["status"] = plan_status

        self.repo.update_business_data(plan_data["_id"], plan_data)
        self.repo.update_local_status(self.business_id, plan_status)
        self.repo.insert_process_tokens_usage(self.tokens_data)

        return {
            "business_id": self.business_id,
            "model": self.model,
            "status": plan_status,
            "updated_costs": new_tokens
        }
