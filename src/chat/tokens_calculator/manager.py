from src.chat.tokens_calculator.cost_calculator import CostCalculator
from src.chat.tokens_calculator.plan_verifier import PlanStatusVerifier
from src.chat.tokens_calculator.repository import BusinessRepository

import logging
from src.chat.utils.logging_utils import setup_logging

setup_logging()

class BusinessPlanManager:
    """Orquestra o cálculo de custos e atualização de plano."""

    def __init__(self, client_id: str, model: str, tokens_data: dict, mongo):
        self.client_id = client_id
        self.model = model
        self.tokens_data = tokens_data
        self.repo = BusinessRepository(mongo)

        logging.info(
            f"[BusinessPlanManager] Inicializado — client_id={client_id}, model={model}"
        )

    def execute(self):
        logging.info(
            f"[BusinessPlanManager] Iniciando processamento de uso — client_id={self.client_id}"
        )

        try:
            # ===== 1. CALCULAR CUSTOS =====
            calculator = CostCalculator(self.model)
            logging.debug(
                f"[BusinessPlanManager] Calculadora criada para modelo={self.model}"
            )

            updated_tokens = calculator.calculate(self.tokens_data)
            logging.info(
                f"[BusinessPlanManager] Cálculo de custos concluído — result={updated_tokens.get('cost')}"
            )

            # ===== 2. BUSCAR DADOS DA EMPRESA =====
            plan_data = self.repo.get_business_data(self.client_id)
            if not plan_data:
                logging.error(
                    f"[BusinessPlanManager] Empresa não encontrada para client_id={self.client_id}"
                )
                raise ValueError(f"Empresa '{self.client_id}' não encontrada.")

            logging.debug(
                f"[BusinessPlanManager] Dados da empresa carregados com sucesso."
            )

            # ===== 3. ATUALIZAR TOKENS =====
            new_tokens = updated_tokens["cost"]

            logging.debug(
                f"[BusinessPlanManager] Atualizando tokens — dados={new_tokens}"
            )

            for k in ["input_tokens", "output_tokens", "total_tokens"]:
                plan_data["plan"]["tokens"][k] += new_tokens[k]

            # ===== 4. ATUALIZAR VALORES DE CUSTO =====
            def format_decimal(value: float) -> str:
                return f"{value:.6f}"

            for k in ["input_cost_usd", "output_cost_usd", "total_cost_usd"]:
                plan_data["plan"]["cost"][k] = str(
                    format_decimal(float(plan_data["plan"]["cost"][k]) + float(new_tokens[k]))
                )

            logging.info(
                f"[BusinessPlanManager] Atualização de custos concluída — valores={plan_data['plan']['cost']}"
            )

            # ===== 5. VERIFICAR STATUS DO PLANO =====
            plan_status = PlanStatusVerifier.verify(plan_data)
            plan_data["plan"]["status"] = plan_status

            logging.info(
                f"[BusinessPlanManager] Status do plano verificado — status={plan_status}"
            )

            # ===== 6. SALVAR NO BANCO =====
            self.repo.update_business_data(plan_data["_id"], plan_data)
            self.repo.update_local_status(self.client_id, plan_status)
            self.repo.insert_process_tokens_usage(self.tokens_data)

            logging.info(
                f"[BusinessPlanManager] Dados salvos com sucesso no repositório."
            )

            # ===== 7. RETORNO =====
            result = {
                "client_id": self.client_id,
                "model": self.model,
                "status": plan_status,
                "updated_costs": new_tokens
            }

            logging.info(
                f"[BusinessPlanManager] Execução finalizada com sucesso — result={result}"
            )

            return result

        except Exception as e:
            logging.error(
                f"[BusinessPlanManager] ERRO durante processamento — client_id={self.client_id}, erro={str(e)}"
            )
            raise
