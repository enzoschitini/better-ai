import json
from bson import ObjectId
from typing import Dict

from utils.mongo_manage import MongoDBManager


# ============================================================
# -------------------- COST CALCULATOR ------------------------
# ============================================================

class CostCalculator:
    """Responsável por calcular e formatar custos de tokens."""

    COST_MODELS = {
        # --- OpenAI ---
        "gpt-4o-mini": {"input": 0.15, "cached_input": 0.075, "output": 0.60},
        "gpt-4o": {"input": 2.50, "cached_input": 1.25, "output": 10.00},
        "gpt-3.5-turbo": {"input": 0.50, "cached_input": 0.25, "output": 1.50},

        # --- Anthropic ---
        "claude-3-haiku": {"input": 0.25, "cached_input": 0.125, "output": 1.25},
        "claude-3-sonnet": {"input": 3.00, "cached_input": 1.50, "output": 15.00},
        "claude-3-opus": {"input": 15.00, "cached_input": 7.50, "output": 75.00},

        # --- Groq ---
        "llama3-8b": {"input": 0.05, "cached_input": 0.025, "output": 0.08},
        "mixtral-8x7b": {"input": 0.20, "cached_input": 0.10, "output": 0.30},
    }

    def __init__(self, model_name: str):
        if model_name not in self.COST_MODELS:
            raise ValueError(f"Modelo '{model_name}' não encontrado.")
        self.model_name = model_name
        self.model_cost = self.COST_MODELS[model_name]

    def _format_decimal(self, value: float) -> str:
        """Formata o número para 6 casas decimais, sem notação científica."""
        return f"{value:.6f}"

    def calculate(self, tokens_response: dict) -> dict:
        """Calcula o custo de input/output e retorna tokens_response atualizado."""
        total_input = tokens_response["tokens_estimados"]["input"]["combined"]["tokens_estimated"]
        total_output = tokens_response["tokens_estimados"]["output"]["tokens_estimated"]

        cost_input = (total_input / 1_000_000) * self.model_cost["input"]
        cost_output = (total_output / 1_000_000) * self.model_cost["output"]
        cost_total = cost_input + cost_output

        tokens_response["cost"] = {
            "modelo": self.model_name,
            "input_tokens": total_input,
            "output_tokens": total_output,
            "total_tokens": total_input + total_output,
            "input_cost_usd": self._format_decimal(cost_input),
            "output_cost_usd": self._format_decimal(cost_output),
            "total_cost_usd": self._format_decimal(cost_total),
        }

        return tokens_response


# ============================================================
# -------------------- PLAN STATUS VERIFIER ------------------
# ============================================================

class PlanStatusVerifier:
    """Verifica se o uso do plano ultrapassou os limites."""

    @staticmethod
    def verify(plan_data: dict) -> str:
        """Retorna 'activated' ou 'no_activated' conforme limites."""
        try:
            plan = plan_data["plan"]
            resource_tokens = plan["resorce"]["tokens"]
            resource_costs = plan["resorce"]["cost"]
            used_tokens = plan["tokens"]
            used_costs = plan["cost"]

            # --- Tokens ---
            if (used_tokens["input_tokens"] > resource_tokens["monthly_budget_input_tokens"] or
                used_tokens["output_tokens"] > resource_tokens["monthly_budget_output_tokens"] or
                used_tokens["total_tokens"] > resource_tokens["monthly_budget_total_tokens"]):
                return "no_activated"

            # --- Custos ---
            if (float(used_costs["input_cost_usd"]) > float(resource_costs["monthly_budget_input_cost_usd"]) or
                float(used_costs["output_cost_usd"]) > float(resource_costs["monthly_budget_output_cost_usd"]) or
                float(used_costs["total_cost_usd"]) > float(resource_costs["monthly_budget_total_cost_usd"])):
                return "no_activated"

            return "activated"

        except KeyError as e:
            raise ValueError(f"Campo ausente no JSON: {e}")


# ============================================================
# -------------------- BUSINESS REPOSITORY -------------------
# ============================================================

class BusinessRepository:
    """Abstrai o acesso ao MongoDB e ao arquivo local JSON."""

    def __init__(self, mongo: MongoDBManager, json_path: str = "business_acess.json"):
        self.mongo = mongo
        self.json_path = json_path

    def get_business_data(self, business_id: str) -> dict:
        """Busca dados da empresa no MongoDB."""
        docs = self.mongo.buscar_documentos(
            "TokensUsage",
            "BusinessAccountManage",
            {"business_id": business_id}
        )
        return docs[0] if docs else None

    def update_business_data(self, mongo_id: str, new_data: dict):
        """Atualiza documento no MongoDB sem alterar o _id."""
        filtro = {'_id': ObjectId(mongo_id)}
        self.mongo.atualizar_documentos(
            "TokensUsage",
            "BusinessAccountManage",
            filtro,
            new_data
        )

    def update_local_status(self, business_id: str, new_status: str):
        """Atualiza o status no arquivo local JSON."""
        with open(self.json_path, "r", encoding="utf-8") as f:
            dados = json.load(f)

        for item in dados:
            if item.get("business_id") == business_id:
                item["status_plan"] = new_status

        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(dados, f, indent=4, ensure_ascii=False)


# ============================================================
# -------------------- BUSINESS PLAN MANAGER -----------------
# ============================================================

class BusinessPlanManager:
    """Orquestra o cálculo de custos e atualização de plano."""

    def __init__(self, business_id: str, model: str, tokens_data: Dict, mongo: MongoDBManager):
        self.business_id = business_id
        self.model = model
        self.tokens_data = tokens_data
        self.repo = BusinessRepository(mongo)

    def execute(self):
        """Fluxo principal: calcula custos, atualiza tokens e verifica status."""
        # 1️⃣ Calcula custos
        calculator = CostCalculator(self.model)
        updated_tokens = calculator.calculate(self.tokens_data)

        # 2️⃣ Busca dados atuais
        plan_data = self.repo.get_business_data(self.business_id)
        if not plan_data:
            raise ValueError(f"Empresa '{self.business_id}' não encontrada no banco.")

        # 3️⃣ Atualiza tokens
        new_tokens = updated_tokens["cost"]
        plan_data["plan"]["tokens"]["input_tokens"] += new_tokens["input_tokens"]
        plan_data["plan"]["tokens"]["output_tokens"] += new_tokens["output_tokens"]
        plan_data["plan"]["tokens"]["total_tokens"] += new_tokens["total_tokens"]

        # 4️⃣ Atualiza custos
        for key in ["input_cost_usd", "output_cost_usd", "total_cost_usd"]:
            plan_data["plan"]["cost"][key] = str(
                float(plan_data["plan"]["cost"][key]) + float(new_tokens[key])
            )

        # 5️⃣ Verifica status do plano
        plan_status = PlanStatusVerifier.verify(plan_data)
        plan_data["plan"]["status"] = plan_status

        # 6️⃣ Persiste no Mongo e JSON
        self.repo.update_business_data(plan_data["_id"], plan_data)
        self.repo.update_local_status(self.business_id, plan_status)

        return {
            "business_id": self.business_id,
            "model": self.model,
            "status": plan_status,
            "updated_costs": new_tokens
        }


# ============================================================
# -------------------- USO DO SCRIPT --------------------------
# ============================================================

if __name__ == "__main__":
    BUSINESS_ID = "0010"
    MODEL = "gpt-4o-mini"
    dic = {
        "tokens_estimados": {
            "input": {"combined": {"tokens_estimated": 2222}},
            "output": {"tokens_estimated": 87}
        }
    }

    mongo = MongoDBManager()
    manager = BusinessPlanManager(BUSINESS_ID, MODEL, dic, mongo)
    resultado = manager.execute()
    print(json.dumps(resultado, indent=4, ensure_ascii=False))
