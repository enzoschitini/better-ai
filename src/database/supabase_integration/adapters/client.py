"""Provedor do cliente síncrono oficial do Supabase (adapter; D-01, D-02).

Cria o cliente de forma PREGUIÇOSA e UMA ÚNICA VEZ (thread-safe). A chave secreta é lida
(``reveal()``) somente aqui e nunca é registrada nem aparece em ``repr``. Os timeouts reais
de rede são configurados nos clientes HTTP (PostgREST e Storage) a partir de
``ConnectionSettings``; o executor de resiliência só aplica orçamento entre tentativas.

Uma função de criação pode ser injetada (testes sem rede).
"""

from __future__ import annotations

import math
import threading
from typing import Any, Callable, Optional

import httpx
from supabase import ClientOptions, create_client

from bai_supabase.contracts.logging import LoggerContract
from bai_supabase.contracts.settings import ConnectionSettings
from bai_supabase.errors.exceptions import ConfigurationError

ClientFactory = Callable[[str, str, Any], Any]
HttpClientFactory = Callable[..., httpx.Client]


class SupabaseClientProvider:
    """Entrega o cliente do SDK (e clientes derivados) a partir de ``ConnectionSettings``."""

    def __init__(
        self,
        settings: ConnectionSettings,
        *,
        storage_timeout_seconds: Optional[float] = None,
        client_factory: Optional[ClientFactory] = None,
        http_client_factory: Optional[HttpClientFactory] = None,
        logger: Optional[LoggerContract] = None,
    ) -> None:
        self._settings = settings
        self._storage_timeout = storage_timeout_seconds
        self._client_factory: ClientFactory = client_factory or create_client
        self._http_factory: HttpClientFactory = http_client_factory or httpx.Client
        self._logger = logger
        self._lock = threading.Lock()
        self._client: Any = None
        self._http: Optional[httpx.Client] = None

    # ------------------------------------------------------------------ acesso
    def client(self) -> Any:
        """Cliente oficial (criado na primeira chamada; as demais devolvem o mesmo objeto)."""
        if self._client is None:
            with self._lock:
                if self._client is None:
                    self._client = self._create()
        return self._client

    def table_client(self) -> Any:
        """Cliente PostgREST (``.schema(nome).from_(tabela)`` / ``.from_(tabela)``)."""
        return self.client().postgrest

    def storage_client(self) -> Any:
        """Cliente de Storage (``.from_(bucket)``)."""
        return self.client().storage

    def http_client(self) -> httpx.Client:
        """Cliente ``httpx`` com a mesma autenticação, para chamadas fora do SDK (ex.: TUS)."""
        if self._http is None:
            with self._lock:
                if self._http is None:
                    self._http = self._create_http()
        return self._http

    @property
    def project_url(self) -> str:
        """URL base do projeto, sem barra final (não é segredo)."""
        return self._settings.url.rstrip("/")

    @property
    def created(self) -> bool:
        return self._client is not None

    def close(self) -> None:
        """Libera o cliente HTTP auxiliar (o cliente do SDK não exige fechamento explícito)."""
        with self._lock:
            http, self._http = self._http, None
        if http is not None:
            http.close()

    def __repr__(self) -> str:
        return f"SupabaseClientProvider(created={self.created})"

    # ------------------------------------------------------------------ criação
    def _require_credentials(self) -> tuple[str, str]:
        url = self._settings.url
        key = self._settings.secret_key.reveal() if self._settings.secret_key else ""
        if not url or not key:
            raise ConfigurationError("URL ou chave secreta ausente na configuração de conexão do Supabase")
        return url, key

    def _options(self) -> ClientOptions:
        s = self._settings
        postgrest_timeout = httpx.Timeout(s.http_timeout_seconds, connect=s.connect_timeout_seconds)
        storage_seconds = self._storage_timeout if self._storage_timeout is not None else s.http_timeout_seconds
        return ClientOptions(
            schema=s.schema,
            auto_refresh_token=False,
            persist_session=False,
            postgrest_client_timeout=postgrest_timeout,
            storage_client_timeout=max(1, math.ceil(storage_seconds)),
        )

    def _create(self) -> Any:
        url, key = self._require_credentials()
        try:
            client = self._client_factory(url, key, self._options())
        except ConfigurationError:
            raise
        except Exception as exc:  # noqa: BLE001 - mensagem fixa: a do SDK pode ecoar entradas
            raise ConfigurationError(
                "não foi possível criar o cliente Supabase (verifique URL e chave de conexão)"
            ) from exc
        if self._logger is not None:
            self._logger.debug("cliente supabase criado", schema=self._settings.schema)
        return client

    def _create_http(self) -> httpx.Client:
        url, key = self._require_credentials()
        s = self._settings
        return self._http_factory(
            base_url=url.rstrip("/"),
            headers={"apikey": key, "Authorization": f"Bearer {key}"},
            timeout=httpx.Timeout(s.http_timeout_seconds, connect=s.connect_timeout_seconds),
        )
