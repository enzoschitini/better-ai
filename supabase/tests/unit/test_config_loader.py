"""SettingsLoader: conversão, validação, erro agregado só com nomes, regras por ambiente."""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from bai_supabase.config import (
    ChainedSource,
    DictSource,
    DotenvFileSource,
    LegacyFallbackSource,
    SettingsLoader,
)
from bai_supabase.errors import ConfigurationError, SettingsError

SECRET = "sb_secret_PLANTED0123456789abcdef"
URL = "https://projetoplantado.supabase.co"
BASE = {"SBX_URL": URL, "SBX_SECRET_KEY": SECRET}
PROD = {**BASE, "SBX_ENV": "prod", "SBX_TABLES_ALLOWLIST": "clientes", "SBX_BUCKETS_ALLOWLIST": "docs"}
SUPABASE_DIR = Path(__file__).resolve().parents[2]


def load(values: dict, **kw):
    return SettingsLoader(**kw).load(DictSource(values))


def error_of(values: dict) -> SettingsError:
    with pytest.raises(SettingsError) as info:
        load(values)
    return info.value


# --- padrões e tipos ------------------------------------------------------------------
def test_minimo_valido_usa_padroes():
    s = load(BASE)
    assert s.connection.url == URL and s.connection.secret_key.reveal() == SECRET
    assert s.connection.publishable_key is None and s.connection.schema == "public"
    assert s.connection.retry_max_attempts == 3 and s.connection.http_timeout_seconds == 10.0
    assert s.storage.signed_url_ttl_seconds == 300 and s.storage.signed_url_max_ttl_seconds == 3600
    assert s.tables.default_page_size == 50 and s.tables.max_page_size == 1000
    assert s.environment.env == "dev" and s.environment.allow_legacy_fallback is False
    assert (s.logging.level, s.logging.color, s.logging.format) == ("DEBUG", "auto", "pretty")


def test_url_sem_barra_final():
    assert load({**BASE, "SBX_URL": URL + "/"}).connection.url == URL


def test_todas_as_variaveis_convertidas():
    s = load({
        **BASE, "SBX_ENV": "DEV", "SBX_PUBLISHABLE_KEY": "sb_publishable_xxxxxxxx", "SBX_DB_SCHEMA": "app",
        "SBX_HTTP_TIMEOUT_SECONDS": "2.5", "SBX_HTTP_CONNECT_TIMEOUT_SECONDS": "1", "SBX_RETRY_MAX_ATTEMPTS": "5",
        "SBX_RETRY_BACKOFF_BASE_SECONDS": "0.1", "SBX_RETRY_BACKOFF_MAX_SECONDS": "4", "SBX_RETRY_BUDGET_SECONDS": "12",
        "SBX_EXPECTED_PROJECT_REF": "ProjetoPlantado",
        "SBX_TABLES_ALLOWLIST": " a , b,a,,", "SBX_TABLES_SERVER_MAX_ROWS": "500", "SBX_TABLES_MAX_PAGE_SIZE": "400",
        "SBX_TABLES_DEFAULT_PAGE_SIZE": "20", "SBX_TABLES_BATCH_SIZE": "100",
        "SBX_TABLES_QUERY_TIMEOUT_SECONDS": "7", "SBX_TABLES_BATCH_TIMEOUT_SECONDS": "70",
        "SBX_BUCKET_DEFAULT": "docs", "SBX_BUCKETS_ALLOWLIST": "docs,imgs", "SBX_BUCKETS_PUBLIC": "imgs",
        "SBX_STORAGE_MAX_FILE_BYTES": "1000", "SBX_STORAGE_ALLOWED_MIME": "Image/*, application/pdf",
        "SBX_STORAGE_SIGNED_URL_TTL_SECONDS": "60", "SBX_STORAGE_SIGNED_URL_MAX_TTL_SECONDS": "120",
        "SBX_STORAGE_UPLOAD_TIMEOUT_SECONDS": "9", "SBX_STORAGE_UPSERT_DEFAULT": "YES",
        "SBX_STORAGE_CACHE_CONTROL_SECONDS": "0", "SBX_STORAGE_RESUMABLE_THRESHOLD_BYTES": "10",
        "SBX_STORAGE_RESUMABLE_CHUNK_BYTES": "20", "SBX_STORAGE_MEMORY_CAP_BYTES": "30",
        "SBX_STORAGE_LIST_PAGE_SIZE": "40", "SBX_STORAGE_DELETE_BATCH_SIZE": "50",
        "SBX_STORAGE_MAX_CONCURRENT_TRANSFERS": "2",
        "SBX_LOG_LEVEL": "warning", "SBX_LOG_COLOR": "ON", "SBX_LOG_FORMAT": "JSON",
        "SBX_LOG_SLOW_MS": "0", "SBX_LOG_MAX_FIELD_CHARS": "20",
    })
    c, t, st, lg = s.connection, s.tables, s.storage, s.logging
    assert (c.schema, c.http_timeout_seconds, c.connect_timeout_seconds, c.retry_max_attempts) == ("app", 2.5, 1.0, 5)
    assert (c.retry_backoff_base_seconds, c.retry_backoff_max_seconds, c.retry_budget_seconds) == (0.1, 4.0, 12.0)
    assert c.publishable_key.reveal() == "sb_publishable_xxxxxxxx"
    assert s.environment.expected_project_ref == "projetoplantado"
    assert t.allowlist == ("a", "b") and (t.server_max_rows, t.max_page_size, t.default_page_size) == (500, 400, 20)
    assert (t.batch_size, t.query_timeout_seconds, t.batch_timeout_seconds) == (100, 7.0, 70.0)
    assert (st.default_bucket, st.buckets_allowlist, st.buckets_public) == ("docs", ("docs", "imgs"), ("imgs",))
    assert st.allowed_mime == ("image/*", "application/pdf") and st.upsert_default is True
    assert (st.max_file_bytes, st.signed_url_ttl_seconds, st.signed_url_max_ttl_seconds) == (1000, 60, 120)
    assert (st.upload_timeout_seconds, st.cache_control_seconds) == (9.0, 0)
    assert (st.resumable_threshold_bytes, st.resumable_chunk_bytes, st.memory_cap_bytes) == (10, 20, 30)
    assert (st.list_page_size, st.delete_batch_size, st.max_concurrent_transfers) == (40, 50, 2)
    assert (lg.level, lg.color, lg.format, lg.slow_ms, lg.max_field_chars) == ("WARNING", "on", "json", 0, 20)


@pytest.mark.parametrize("raw,expected", [("true", True), ("1", True), ("YES", True), ("false", False), ("0", False), ("No", False)])
def test_booleanos_aceitos(raw, expected):
    assert load({**BASE, "SBX_STORAGE_UPSERT_DEFAULT": raw}).storage.upsert_default is expected


def test_vazio_conta_como_ausente_e_usa_padrao():
    s = load({**BASE, "SBX_LOG_LEVEL": "   ", "SBX_DB_SCHEMA": "", "SBX_RETRY_MAX_ATTEMPTS": ""})
    assert s.logging.level == "DEBUG" and s.connection.schema == "public" and s.connection.retry_max_attempts == 3


def test_tamanhos_de_pagina_derivam_do_server_max_rows():
    s = load({**BASE, "SBX_TABLES_SERVER_MAX_ROWS": "30"})
    assert (s.tables.max_page_size, s.tables.default_page_size) == (30, 30)


# --- ausência (obrigatórias) -------------------------------------------------------------
@pytest.mark.parametrize("name", ["SBX_URL", "SBX_SECRET_KEY"])
@pytest.mark.parametrize("value", [None, "", "  "])
def test_obrigatoria_ausente_ou_vazia(name, value):
    values = {**BASE, name: value}
    if value is None:
        del values[name]
    err = error_of(values)
    assert err.missing == [name] and err.invalid == []


# --- valores inválidos: um caso por variável ---------------------------------------------
INVALID = {
    "SBX_ENV": "staging", "SBX_URL": "http://projeto.supabase.co", "SBX_SECRET_KEY": "sb_publishable_xxxxxxxx",
    "SBX_PUBLISHABLE_KEY": "sb_secret_xxxxxxxx", "SBX_DB_SCHEMA": "a b;drop",
    "SBX_HTTP_TIMEOUT_SECONDS": "0", "SBX_HTTP_CONNECT_TIMEOUT_SECONDS": "abc", "SBX_RETRY_MAX_ATTEMPTS": "0",
    "SBX_RETRY_BACKOFF_BASE_SECONDS": "-1", "SBX_RETRY_BACKOFF_MAX_SECONDS": "nan", "SBX_RETRY_BUDGET_SECONDS": "0",
    "SBX_EXPECTED_PROJECT_REF": "Inv@lido!", "SBX_ALLOW_LEGACY_FALLBACK": "talvez",
    "SBX_TABLES_ALLOWLIST": "ok,tabela invalida", "SBX_TABLES_DEFAULT_PAGE_SIZE": "1.5",
    "SBX_TABLES_MAX_PAGE_SIZE": "0", "SBX_TABLES_BATCH_SIZE": "-3", "SBX_TABLES_SERVER_MAX_ROWS": "x",
    "SBX_TABLES_QUERY_TIMEOUT_SECONDS": "0", "SBX_TABLES_BATCH_TIMEOUT_SECONDS": "-5",
    "SBX_BUCKET_DEFAULT": "../etc", "SBX_BUCKETS_ALLOWLIST": "ok,../x", "SBX_BUCKETS_PUBLIC": "a/b",
    "SBX_STORAGE_MAX_FILE_BYTES": "0", "SBX_STORAGE_ALLOWED_MIME": "texto-sem-barra",
    "SBX_STORAGE_SIGNED_URL_TTL_SECONDS": "0", "SBX_STORAGE_SIGNED_URL_MAX_TTL_SECONDS": "1_0",
    "SBX_STORAGE_UPLOAD_TIMEOUT_SECONDS": "0", "SBX_STORAGE_UPSERT_DEFAULT": "2",
    "SBX_STORAGE_CACHE_CONTROL_SECONDS": "-1", "SBX_STORAGE_RESUMABLE_THRESHOLD_BYTES": "0",
    "SBX_STORAGE_RESUMABLE_CHUNK_BYTES": "0", "SBX_STORAGE_MEMORY_CAP_BYTES": "0",
    "SBX_STORAGE_LIST_PAGE_SIZE": "0", "SBX_STORAGE_DELETE_BATCH_SIZE": "0", "SBX_STORAGE_MAX_CONCURRENT_TRANSFERS": "0",
    "SBX_LOG_LEVEL": "TRACE", "SBX_LOG_COLOR": "rainbow", "SBX_LOG_FORMAT": "xml",
    "SBX_LOG_SLOW_MS": "-1", "SBX_LOG_MAX_FIELD_CHARS": "19",
}


@pytest.mark.parametrize("name,value", sorted(INVALID.items()))
def test_valor_invalido_cita_so_o_nome(name, value):
    err = error_of({**BASE, name: value})
    assert name in [n for n, _ in err.invalid]
    reasons = " ".join(reason for _, reason in err.invalid)
    assert value not in reasons or len(value) < 3  # regra nunca repete o valor
    assert value not in str(err) or len(value) < 3 or value in name


def test_todas_as_variaveis_tem_caso_invalido_ou_sao_livres():
    livres = {"SBX_DB_CONNECTION_STRING"}  # reservada, sem validação
    assert set(SettingsLoader.variable_names()) - set(INVALID) - livres == set()


# --- padrão por variável (valor ausente => default) ----------------------------------------
@pytest.mark.parametrize("name", [n for n in SettingsLoader.variable_names() if n not in ("SBX_URL", "SBX_SECRET_KEY")])
def test_cada_parametro_opcional_aceita_ausencia(name):
    load(BASE)  # nenhum opcional é exigido em dev
    assert name not in BASE


# --- coerência -----------------------------------------------------------------------------
def test_base_maior_que_max_e_invalido():
    err = error_of({**BASE, "SBX_RETRY_BACKOFF_BASE_SECONDS": "10", "SBX_RETRY_BACKOFF_MAX_SECONDS": "2"})
    assert [n for n, _ in err.invalid] == ["SBX_RETRY_BACKOFF_MAX_SECONDS"]


def test_ttl_maior_que_teto_e_invalido():
    err = error_of({**BASE, "SBX_STORAGE_SIGNED_URL_TTL_SECONDS": "7200"})
    assert [n for n, _ in err.invalid] == ["SBX_STORAGE_SIGNED_URL_TTL_SECONDS"]


def test_pagina_padrao_maior_que_max_e_max_maior_que_servidor():
    err = error_of({**BASE, "SBX_TABLES_DEFAULT_PAGE_SIZE": "200", "SBX_TABLES_MAX_PAGE_SIZE": "100"})
    assert [n for n, _ in err.invalid] == ["SBX_TABLES_DEFAULT_PAGE_SIZE"]
    err = error_of({**BASE, "SBX_TABLES_SERVER_MAX_ROWS": "100", "SBX_TABLES_MAX_PAGE_SIZE": "500"})
    assert [n for n, _ in err.invalid] == ["SBX_TABLES_MAX_PAGE_SIZE"]


def test_bucket_padrao_deve_estar_na_allowlist():
    err = error_of({**BASE, "SBX_BUCKET_DEFAULT": "c", "SBX_BUCKETS_ALLOWLIST": "a,b"})
    assert [n for n, _ in err.invalid] == ["SBX_BUCKET_DEFAULT"]


def test_url_com_credenciais_query_ou_fragmento_invalida():
    for url in ("https://u:p@x.supabase.co", "https://x.supabase.co?a=1", "https://x.supabase.co#f", "https://"):
        assert [n for n, _ in error_of({**BASE, "SBX_URL": url}).invalid] == ["SBX_URL"]


def test_http_so_para_loopback_em_dev():
    assert load({**BASE, "SBX_URL": "http://127.0.0.1:54321"}).connection.url == "http://127.0.0.1:54321"
    assert load({**BASE, "SBX_URL": "http://localhost:54321"}).connection.url == "http://localhost:54321"
    err = error_of({**PROD, "SBX_URL": "http://127.0.0.1:54321"})
    assert [n for n, _ in err.invalid] == ["SBX_URL"]


def test_expected_project_ref_deve_casar_com_a_url():
    assert load({**BASE, "SBX_EXPECTED_PROJECT_REF": "projetoplantado"}).environment.expected_project_ref == "projetoplantado"
    err = error_of({**BASE, "SBX_EXPECTED_PROJECT_REF": "outroprojeto"})
    assert [n for n, _ in err.invalid] == ["SBX_EXPECTED_PROJECT_REF"]


# --- erro agregado ---------------------------------------------------------------------------
def test_erro_agrega_todos_os_problemas_sem_valores():
    err = error_of({
        "SBX_ENV": "prod", "SBX_HTTP_TIMEOUT_SECONDS": "valor-invalido-plantado", "SBX_LOG_LEVEL": "nivel-plantado",
        "SBX_SECRET_KEY": "",
    })
    assert err.missing == ["SBX_URL", "SBX_SECRET_KEY", "SBX_TABLES_ALLOWLIST", "SBX_BUCKETS_ALLOWLIST"]
    assert [n for n, _ in err.invalid] == ["SBX_HTTP_TIMEOUT_SECONDS", "SBX_LOG_LEVEL"]
    text = str(err)
    assert "ambiente: prod" in text and "Ausentes (obrigatórias):" in text and "Inválidas:" in text
    assert "- SBX_HTTP_TIMEOUT_SECONDS: deve ser número > 0" in text
    assert "- SBX_LOG_LEVEL: deve ser um de DEBUG, INFO, WARNING, ERROR" in text
    assert "supabase/spec/research/01-variaveis-de-ambiente.md" in text and "supabase/.env.example" in text
    assert "plantado" not in text
    assert isinstance(err, ConfigurationError)


def test_segredo_plantado_nunca_aparece_no_erro():
    err = error_of({**BASE, "SBX_ENV": "prod", "SBX_HTTP_TIMEOUT_SECONDS": "x"})
    blob = f"{err!s} {err!r} {err.missing} {err.invalid} {err.to_dict()}"
    assert SECRET not in blob and URL not in blob


def test_chave_publishable_na_secret_nao_vaza_valor():
    value = "sb_publishable_PLANTED0123456789"
    err = error_of({**BASE, "SBX_SECRET_KEY": value})
    assert value not in f"{err} {err.invalid}"


def test_ambiente_invalido_indefinido_na_mensagem():
    err = error_of({**BASE, "SBX_ENV": "staging"})
    assert "ambiente: indefinido" in str(err) and [n for n, _ in err.invalid] == ["SBX_ENV"]


# --- regras por ambiente -------------------------------------------------------------------
@pytest.mark.parametrize(
    "env,expected",
    [("dev", ("DEBUG", "auto", "pretty")), ("homol", ("INFO", "auto", "pretty")), ("prod", ("WARNING", "off", "json"))],
)
def test_padroes_de_log_por_ambiente(env, expected):
    s = load({**PROD, "SBX_ENV": env})
    assert (s.logging.level, s.logging.color, s.logging.format) == expected


def test_explicito_vence_padrao_do_ambiente():
    s = load({**PROD, "SBX_LOG_LEVEL": "error", "SBX_LOG_COLOR": "on", "SBX_LOG_FORMAT": "pretty"})
    assert (s.logging.level, s.logging.color, s.logging.format) == ("ERROR", "on", "pretty")


def test_prod_exige_allowlists():
    err = error_of({**BASE, "SBX_ENV": "prod"})
    assert err.missing == ["SBX_TABLES_ALLOWLIST", "SBX_BUCKETS_ALLOWLIST"]
    assert load(PROD).environment.env == "prod"


def test_prod_allowlist_invalida_nao_conta_como_ausente():
    err = error_of({**PROD, "SBX_TABLES_ALLOWLIST": "x y"})
    assert err.missing == [] and [n for n, _ in err.invalid] == ["SBX_TABLES_ALLOWLIST"]


def test_dev_e_homol_nao_exigem_allowlists_homol_avisa():
    assert load(BASE).tables.allowlist == ()
    loader = SettingsLoader()
    loader.load(DictSource({**BASE, "SBX_ENV": "homol"}))
    assert loader.warnings == ["SBX_TABLES_ALLOWLIST recomendada em homol", "SBX_BUCKETS_ALLOWLIST recomendada em homol"]


@pytest.mark.parametrize("env", ["homol", "prod"])
def test_fallback_legado_proibido_em_homol_e_prod(env):
    err = error_of({**PROD, "SBX_ENV": env, "SBX_ALLOW_LEGACY_FALLBACK": "true"})
    assert [n for n, _ in err.invalid] == ["SBX_ALLOW_LEGACY_FALLBACK"]


def test_fallback_legado_permitido_em_dev():
    assert load({**BASE, "SBX_ALLOW_LEGACY_FALLBACK": "true"}).environment.allow_legacy_fallback is True


@pytest.mark.parametrize("env", ["homol", "prod"])
def test_valor_vindo_do_fallback_legado_proibido_em_homol_e_prod(env):
    inner = DictSource({"SBX_ENV": env, "SUPABASE_URL": URL, "SUPABASE_SECRET_KEY": SECRET,
                        "SBX_TABLES_ALLOWLIST": "t", "SBX_BUCKETS_ALLOWLIST": "b"})
    err = None
    with pytest.raises(SettingsError) as info:
        SettingsLoader().load(LegacyFallbackSource(inner, enabled=True))
    err = info.value
    assert [n for n, _ in err.invalid] == ["SBX_URL", "SBX_SECRET_KEY"]
    assert SECRET not in str(err)


def test_fallback_legado_funciona_em_dev():
    inner = DictSource({"SUPABASE_URL": URL, "SUPABASE_SECRET_KEY": SECRET})
    s = SettingsLoader().load(LegacyFallbackSource(inner, enabled=True))
    assert s.connection.url == URL and s.connection.secret_key.reveal() == SECRET


@pytest.mark.parametrize("env", ["homol", "prod"])
def test_dotenv_de_arquivo_proibido_em_homol_e_prod(env, tmp_path):
    path = tmp_path / ".env"
    path.write_text("\n".join(f"{k}={v}" for k, v in {**PROD, "SBX_ENV": env}.items()), encoding="utf-8")
    with pytest.raises(SettingsError) as info:
        SettingsLoader().load(DotenvFileSource(path))
    assert [n for n, _ in info.value.invalid] == ["SBX_ENV"]
    assert SECRET not in str(info.value)


def test_dotenv_de_arquivo_permitido_em_dev_e_encadeado(tmp_path):
    path = tmp_path / ".env"
    path.write_text(f"SBX_URL={URL}\nSBX_SECRET_KEY=do-arquivo-plantado\nSBX_LOG_LEVEL=INFO\n", encoding="utf-8")
    chain = ChainedSource(DictSource({"SBX_LOG_LEVEL": "ERROR"}), DotenvFileSource(path))
    s = SettingsLoader().load(chain)
    assert s.logging.level == "ERROR" and s.connection.secret_key.reveal() == "do-arquivo-plantado"


# --- avisos de variável desconhecida ---------------------------------------------------------
def test_variavel_desconhecida_gera_aviso_so_com_nome():
    from tests.fakes.logger import CaptureLogger

    log = CaptureLogger()
    loader = SettingsLoader(log)
    loader.load(DictSource({**BASE, "SBX_LOG_LEVl": "valor-plantado", "SBX_TEST_URL": "x", "OUTRA": "y"}))
    assert loader.warnings == ["variável desconhecida (erro de digitação?): SBX_LOG_LEVl"]
    assert "valor-plantado" not in repr(loader.warnings) + repr(log.events)
    assert log.levels() == ["WARNING"]


def test_avisos_reiniciam_a_cada_load_e_sobrevivem_ao_erro():
    loader = SettingsLoader()
    loader.load(DictSource({**BASE, "SBX_TYPO": "x"}))
    assert len(loader.warnings) == 1
    loader.load(DictSource(BASE))
    assert loader.warnings == []
    with pytest.raises(SettingsError):
        loader.load(DictSource({"SBX_TYPO": "x"}))
    assert len(loader.warnings) == 1


def test_connection_string_reservada_gera_aviso_sem_valor():
    loader = SettingsLoader()
    loader.load(DictSource({**BASE, "SBX_DB_CONNECTION_STRING": "postgresql://u:senha-plantada@h/db"}))
    assert loader.warnings == ["SBX_DB_CONNECTION_STRING definida, mas reservada e ignorada na v1"]


def test_fonte_sem_names_nao_gera_aviso():
    class SoGet:
        def get(self, name):
            return BASE.get(name)

    loader = SettingsLoader()
    loader.load(SoGet())
    assert loader.warnings == []


# --- consistência com os modelos .env.example -------------------------------------------------
def names_in(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    return re.findall(r"^([A-Z][A-Z0-9_]*)=", text, flags=re.MULTILINE)


def test_env_example_tem_exatamente_os_nomes_do_loader():
    found = names_in(SUPABASE_DIR / ".env.example")
    assert sorted(found) == sorted(SettingsLoader.variable_names())
    assert len(found) == len(set(found))


def test_env_example_nao_tem_valores():
    for line in (SUPABASE_DIR / ".env.example").read_text(encoding="utf-8").splitlines():
        if re.match(r"^[A-Z][A-Z0-9_]*=", line):
            assert line.split("=", 1)[1] == "", line


def test_env_test_example_so_nomes_de_teste():
    path = SUPABASE_DIR / ".env.test.example"
    assert sorted(names_in(path)) == sorted([
        "SBX_TEST_URL", "SBX_TEST_SECRET_KEY", "SBX_TEST_ALLOW_LIVE", "SBX_TEST_BUCKET", "SBX_TEST_PROJECT_REF",
    ])
    for line in path.read_text(encoding="utf-8").splitlines():
        if re.match(r"^[A-Z][A-Z0-9_]*=", line):
            assert line.split("=", 1)[1] == "", line


def test_loader_le_todos_os_nomes_declarados():
    seen: set[str] = set()

    class Recording(DictSource):
        def get(self, name):
            seen.add(name)
            return super().get(name)

    SettingsLoader().load(Recording(BASE))
    assert seen == set(SettingsLoader.variable_names())


def test_nomes_com_prefixo_e_sem_duplicata():
    names = SettingsLoader.variable_names()
    assert len(names) == len(set(names)) and all(n.startswith("SBX_") for n in names)
    assert "SBX_MAX_RETRIES" not in names and "SBX_RETRY_MAX_ATTEMPTS" in names


# --- ambiente real não é tocado -----------------------------------------------------------------
def test_loader_so_usa_a_fonte_recebida(monkeypatch):
    monkeypatch.setenv("SBX_URL", "https://do-ambiente-real.supabase.co")
    monkeypatch.setenv("SBX_SECRET_KEY", "do-ambiente-real")
    err = error_of({})
    assert err.missing == ["SBX_URL", "SBX_SECRET_KEY"]


def test_loader_e_settings_nao_leem_os_environ_fora_de_sources():
    root = SUPABASE_DIR / "bai_supabase"
    offenders = [
        str(p.relative_to(root)) for p in root.rglob("*.py")
        if p.name != "sources.py" and re.search(r"os\.environ|getenv", p.read_text(encoding="utf-8"))
    ]
    assert offenders == []
