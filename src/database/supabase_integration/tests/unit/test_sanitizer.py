"""Sanitizador: o "segredo plantado" nunca pode aparecer na saída (research/02 §10.3)."""
from __future__ import annotations

import json

import pytest

from src.database.supabase_integration.contracts.secret import Secret
from src.database.supabase_integration.logging.sanitizer import MASK, sanitize, sanitize_fields

JWT = "eyJhbGciOiJIUzI1NiJ9.eyJyb2xlIjoicGxhbnRhZG8ifQ.c2lnbmF0dXJhUExBTlRBREE"
SB_SECRET = "sb_secret_PLANTED0123456789abcdef"
SB_PUBLISHABLE = "sb_publishable_PLANTED0123456789abcdef"
PASSWORD = "S3nhaPlantada!42"


@pytest.mark.parametrize(
    "text",
    [
        f"falhou com {JWT} no meio",
        f"chave={SB_SECRET}",
        f"chave {SB_PUBLISHABLE}.",
        f"Authorization: Bearer {JWT}",
        f"apikey: {SB_SECRET}",
        f"x-api-key={SB_SECRET}",
        f"Bearer {SB_SECRET}",
        f"https://abc.supabase.co/storage/v1/object/sign/docs/a.pdf?token={JWT}",
        f"https://abc.supabase.co/rest/v1/t?select=*&apikey={SB_SECRET}",
        f"postgresql://postgres:{PASSWORD}@db.abc.supabase.co:5432/postgres",
        f"host=db user=app password={PASSWORD} dbname=x",
        f'{{"password": "{PASSWORD}"}}',
        f"db_password={PASSWORD}",
        f"https://user:{PASSWORD}@host.example/path",
    ],
)
def test_segredo_plantado_nao_aparece(text):
    out = sanitize(text)
    for planted in (JWT, SB_SECRET, SB_PUBLISHABLE, PASSWORD):
        assert planted not in out, out
    assert MASK in out


def test_texto_comum_fica_intacto():
    assert sanitize("upload concluido") == "upload concluido"
    assert sanitize("max_tokens=5 tokens_used=3") == "max_tokens=5 tokens_used=3"


def test_scalars_passam_sem_alteracao():
    assert sanitize(10) == 10
    assert sanitize(1.5) == 1.5
    assert sanitize(True) is True
    assert sanitize(None) is None


def test_float_nao_finito_vira_texto():
    assert sanitize(float("nan")) == "nan"


def test_secret_e_mascarado_em_qualquer_posicao():
    s = Secret("valor-super-secreto")
    assert sanitize(s) == MASK
    out = sanitize({"a": [s, {"b": s}]})
    assert "valor-super-secreto" not in json.dumps(out)
    assert out["a"][0] == MASK


@pytest.mark.parametrize(
    "key",
    ["apikey", "API-KEY", "Authorization", "token", "access_token", "refresh_token",
     "secret", "password", "senha", "cookie", "db_token", "signed_url", "x-api-key"],
)
def test_chaves_sensiveis_de_dicionario_sao_mascaradas(key):
    out = sanitize({key: "valor-qualquer-123", "ok": "visivel"})
    assert out[key] == MASK
    assert out["ok"] == "visivel"


def test_chaves_nao_sensiveis_parecidas_passam():
    out = sanitize({"max_tokens": 5, "primary_key": "id"})
    assert out == {"max_tokens": 5, "primary_key": "id"}


def test_url_assinada_perde_a_query():
    url = f"https://abc.supabase.co/storage/v1/object/sign/docs/a.pdf?token={JWT}&x=1"
    out = sanitize(url)
    assert out == "https://abc.supabase.co/storage/v1/object/sign/docs/a.pdf?***"


def test_url_comum_mantem_caminho():
    out = sanitize("https://abc.supabase.co/rest/v1/clientes?select=id")
    assert out == "https://abc.supabase.co/rest/v1/clientes?select=id"


def test_string_de_conexao_inteira_mascarada():
    out = sanitize(f"erro em postgres://u:{PASSWORD}@h:5432/db agora")
    assert out == f"erro em postgres://{MASK} agora"


def test_failing_row_do_postgres_e_removido():
    msg = (
        'null value in column "nome" violates not-null constraint. '
        "Failing row contains (42, joao@example.com, 123.456.789-00)."
    )
    out = sanitize(msg)
    assert "joao" not in out and "123.456" not in out
    assert "Failing row contains (***)" in out
    assert "violates not-null constraint" in out


def test_valor_de_chave_duplicada_e_removido():
    out = sanitize("Key (email)=(maria@exemplo.com) already exists.")
    assert out == f"Key (email)=({MASK}) already exists."


def test_email_e_mascarado():
    assert sanitize("filtro maria.silva@exemplo.com.br ativo") == f"filtro m{MASK}@exemplo.com.br ativo"


def test_truncamento_por_max_chars():
    out = sanitize("a" * 500, max_chars=50)
    assert out.startswith("a" * 50)
    assert "[+450 chars]" in out
    assert len(out) < 80


def test_max_chars_zero_desliga_truncamento():
    assert sanitize("a" * 500, max_chars=0) == "a" * 500


def test_mascara_antes_de_truncar_nao_deixa_pedaco_do_segredo():
    text = "x" * 30 + f" token={SB_SECRET}"
    out = sanitize(text, max_chars=40)
    assert "sb_secret" not in out and "PLANTED" not in out


def test_extra_secrets_str_e_secret():
    out = sanitize("a senha hunter2-planted vazou; outra: outro-planted-9", extra_secrets=["hunter2-planted", Secret("outro-planted-9")])
    assert "planted" not in out
    assert out.count(MASK) == 2


def test_extra_secrets_curtos_sao_ignorados():
    assert sanitize("abc abc", extra_secrets=["abc"]) == "abc abc"


def test_bytes_nunca_vao_para_o_log():
    assert sanitize(b"conteudo do arquivo") == "<19 bytes>"


def test_excecao_vira_texto_sanitizado():
    out = sanitize(RuntimeError(f"falha com {SB_SECRET}"))
    assert out.startswith("RuntimeError: ")
    assert SB_SECRET not in out


def test_estruturas_aninhadas_e_listas():
    out = sanitize_fields(
        {"headers": {"Authorization": f"Bearer {JWT}", "accept": "json"}, "items": [f"k={SB_SECRET}", 3]}
    )
    dump = json.dumps(out)
    assert JWT not in dump and SB_SECRET not in dump
    assert out["headers"]["accept"] == "json"
    assert out["items"][1] == 3


def test_listas_longas_sao_cortadas():
    out = sanitize(list(range(500)))
    assert len(out) == 51
    assert "items" in out[-1]


def test_profundidade_limitada():
    deep: dict = {}
    cur = deep
    for _ in range(20):
        cur["n"] = {}
        cur = cur["n"]
    assert "<...>" in json.dumps(sanitize(deep))


def test_chave_de_dict_tambem_e_sanitizada():
    out = sanitize({SB_SECRET: 1})
    assert SB_SECRET not in json.dumps(out)


def test_resultado_e_serializavel_em_json():
    class Estranho:
        def __str__(self) -> str:
            return "estranho"

    out = sanitize_fields({"obj": Estranho(), "set": {1}, "t": (1, 2), "b": b"x", "e": ValueError("x")})
    json.dumps(out, allow_nan=False)
