import json
import logging
from src.chat.utils.logging_utils import setup_logging

setup_logging()

class BusinessVerifier:
    #logging.info("Verificando informações da empresa")
    """Classe responsável por verificar se o plano de uma empresa está ativo."""

    def __init__(self, caminho_arquivo: str):
        self.caminho_arquivo = caminho_arquivo
        self.dados = self._carregar_dados()

    def _carregar_dados(self):
        """Carrega os dados do arquivo JSON."""
        try:
            with open(self.caminho_arquivo, "r", encoding="utf-8") as arquivo:
                return json.load(arquivo)
        except FileNotFoundError:
            #print(f"❌ Arquivo não encontrado: {self.caminho_arquivo}")
            return []
        except json.JSONDecodeError:
            #print(f"❌ Erro ao decodificar o JSON em {self.caminho_arquivo}")
            return []

    def plano_ativo(self, client_id: str) -> bool:
        """Retorna True se o plano da empresa estiver ativo."""
        for empresa in self.dados:
            if empresa["client_id"] == client_id:
                return empresa["status_plan"].lower() == "activated"  # ✅ corrigido
        return False  # Caso o ID não exista

    def verificar(self, client_id: str):
        """Retorna o status textual do plano."""
        return "activated" if self.plano_ativo(client_id) else "deactivated"