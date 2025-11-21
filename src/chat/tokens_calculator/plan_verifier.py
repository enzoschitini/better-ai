import logging

logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(filename)s - line: %(lineno)d - %(levelname)s - %(message)s'
)

class PlanStatusVerifier:
    """Verifica se o uso do plano ultrapassou os limites."""

    @staticmethod
    def verify(plan_data: dict) -> str:
        logging.info("Iniciando verificação de status do plano.")

        try:
            logging.info("Extraindo dados do plano...")
            plan = plan_data["plan"]
            resource_tokens = plan["resorce"]["tokens"]
            resource_costs = plan["resorce"]["cost"]
            used_tokens = plan["tokens"]
            used_costs = plan["cost"]

            logging.info(
                f"Tokens usados: input={used_tokens['input_tokens']}, "
                f"output={used_tokens['output_tokens']}, total={used_tokens['total_tokens']}"
            )
            logging.info(
                f"Limites de tokens: input={resource_tokens['monthly_budget_input_tokens']}, "
                f"output={resource_tokens['monthly_budget_output_tokens']}, "
                f"total={resource_tokens['monthly_budget_total_tokens']}"
            )

            # Verifica limites de tokens
            if (
                used_tokens["input_tokens"] > resource_tokens["monthly_budget_input_tokens"] or
                used_tokens["output_tokens"] > resource_tokens["monthly_budget_output_tokens"] or
                used_tokens["total_tokens"] > resource_tokens["monthly_budget_total_tokens"]
            ):
                logging.warning("Limite de tokens excedido.")
                return "no_activated"

            logging.info(
                f"Custos usados: input={used_costs['input_cost_usd']}, "
                f"output={used_costs['output_cost_usd']}, total={used_costs['total_cost_usd']}"
            )
            logging.info(
                f"Limites de custos: input={resource_costs['monthly_budget_input_cost_usd']}, "
                f"output={resource_costs['monthly_budget_output_cost_usd']}, "
                f"total={resource_costs['monthly_budget_total_cost_usd']}"
            )

            # Verifica limites de custos
            if (
                float(used_costs["input_cost_usd"]) > float(resource_costs["monthly_budget_input_cost_usd"]) or
                float(used_costs["output_cost_usd"]) > float(resource_costs["monthly_budget_output_cost_usd"]) or
                float(used_costs["total_cost_usd"]) > float(resource_costs["monthly_budget_total_cost_usd"])
            ):
                logging.warning("Limite de custos excedido.")
                return "no_activated"

            logging.info("Plano dentro dos limites. Status: activated.")
            return "activated"

        except KeyError as e:
            logging.error(f"Campo ausente no JSON: {e}")
            raise ValueError(f"Campo ausente no JSON: {e}")

        except Exception as e:
            logging.exception("Erro inesperado ao verificar o plano.")
            raise
