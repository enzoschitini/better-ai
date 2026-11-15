"""Ponto de composição único da integração Supabase para o resto do projeto.

Os fluxos (agentes, serviços, rotas) nunca montam clientes do SDK: pedem a integração aqui.
A configuração vem das variáveis ``SBX_*`` (ver ``src/database/supabase_integration/.env.example``).
"""

from functools import lru_cache
from typing import Iterable

from dotenv import load_dotenv

from src.database.supabase_integration import TableDescriptor, create_integration_from_env
from src.database.supabase_integration.facade.integration import SupabaseIntegration

load_dotenv()  # mesmo comportamento dos demais módulos: .env local alimenta o ambiente do processo


@lru_cache(maxsize=1)
def get_supabase() -> SupabaseIntegration:
    """Integração compartilhada do processo (criada na primeira chamada).

    Falha cedo com ``SettingsError`` listando só os NOMES das variáveis ``SBX_*`` ausentes/inválidas.
    """
    return create_integration_from_env(descriptors=_table_descriptors())


def _table_descriptors() -> Iterable[TableDescriptor]:
    # Declare aqui as tabelas acessadas pelos fluxos (hoje nenhum fluxo usa tabelas do Supabase).
    return ()
