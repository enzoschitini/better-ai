"""Logger: níveis, ANSI, formatos, truncamento, lentidão e ausência de segredos."""
from __future__ import annotations

import io
import json
import re
from datetime import datetime, timezone

import pytest

from bai_supabase.contracts.logging import LoggerContract
from bai_supabase.contracts.secret import Secret
from bai_supabase.contracts.settings import LoggingSettings
from bai_supabase.errors import ConfigurationError
from bai_supabase.logging import StructuredLogger, build_logger

ANSI = re.compile(r"\x1b\[[0-9;]*m")
SB_SECRET = "sb_secret_PLANTED0123456789abcdef"
JWT = "eyJhbGciOiJIUzI1NiJ9.eyJyb2xlIjoicGxhbnRhZG8ifQ.c2lnbmF0dXJhUExBTlRBREE"
FIXED = datetime(2026, 11, 14, 9, 8, 7, 123456, tzinfo=timezone.utc)


class FakeTTY(io.StringIO):
    def isatty(self) -> bool:
        return True


def make(stream=None, **overrides):
    stream = stream if stream is not None else io.StringIO()
    settings = LoggingSettings(**{"level": "DEBUG", "color": "off", "format": "pretty", **overrides})
    return build_logger(settings, stream, clock=lambda: FIXED, no_color=False), stream


def lines(stream) -> list[str]:
    return [ln for ln in stream.getvalue().splitlines() if ln]


def test_implementa_o_contrato():
    log, _ = make()
    assert isinstance(log, LoggerContract)


# --- níveis -------------------------------------------------------------------
@pytest.mark.parametrize(
    "level,expected",
    [("DEBUG", 4), ("INFO", 3), ("WARNING", 2), ("ERROR", 1)],
)
def test_filtra_por_nivel(level, expected):
    log, out = make(level=level)
    log.debug("d")
    log.info("i")
    log.warning("w")
    log.error("e")
    assert len(lines(out)) == expected


def test_nivel_e_case_insensitive_e_invalido_falha():
    log, out = make(level="info")
    log.debug("x")
    log.info("y")
    assert len(lines(out)) == 1
    with pytest.raises(ConfigurationError):
        make(level="TRACE")
    with pytest.raises(ConfigurationError):
        make(color="rainbow")
    with pytest.raises(ConfigurationError):
        make(format="xml")


def test_nivel_textual_sempre_presente():
    for color in ("off", "on"):
        log, out = make(color=color)
        log.warning("cuidado")
        assert "WARNING" in ANSI.sub("", out.getvalue())


# --- formato pretty ---------------------------------------------------------------
def test_pretty_uma_linha_com_hora_nivel_evento_e_campos():
    log, out = make()
    log.info("tabela consultada", resource="clientes", duration_ms=12, operation="select", count=3)
    (line,) = lines(out)
    assert line == "09:08:07.123 INFO    tabela consultada operation=select resource=clientes count=3 duration_ms=12"


def test_pretty_valores_com_espaco_ou_quebra_de_linha_ficam_em_uma_linha():
    log, out = make()
    log.info("evento\ncom quebra", detalhe="a b\nc", nada=None, ok=True, lista=[1, 2])
    (line,) = lines(out)
    assert '"a b\\nc"' in line
    assert "nada=null" in line and "ok=true" in line and "lista=[1,2]" in line
    assert "\n" not in line


def test_pretty_correlation_id_por_ultimo():
    log, out = make()
    log.bind(correlation_id="abc").info("x", zeta=1, alfa=2)
    assert lines(out)[0].endswith("alfa=2 zeta=1 correlation_id=abc")


# --- formato json -----------------------------------------------------------------
def test_json_e_uma_linha_valida():
    log, out = make(format="json")
    log.error("falhou", operation="upload", status=500, retryable=False, nested={"a": [1, None]})
    (line,) = lines(out)
    data = json.loads(line)
    assert data == {
        "ts": "2026-11-14T09:08:07.123456+00:00",
        "level": "ERROR",
        "event": "falhou",
        "operation": "upload",
        "status": 500,
        "retryable": False,
        "nested": {"a": [1, None]},
    }


def test_json_nunca_tem_ansi_mesmo_com_cor_on():
    log, out = make(format="json", color="on")
    log.info("x")
    assert "\x1b" not in out.getvalue()
    json.loads(lines(out)[0])


def test_json_colisao_de_campos_reservados_nao_sobrescreve():
    log, out = make(format="json")
    log.info("real", level="x", ts="y", event="z")
    data = json.loads(lines(out)[0])
    assert data["event"] == "real" and data["level"] == "INFO"
    assert data["field_level"] == "x" and data["field_ts"] == "y" and data["field_event"] == "z"


def test_json_quebra_de_linha_no_valor_continua_uma_linha():
    log, out = make(format="json")
    log.info("x", texto="a\nb")
    assert len(lines(out)) == 1
    assert json.loads(lines(out)[0])["texto"] == "a\nb"


# --- cores -----------------------------------------------------------------------
def test_cor_on_tem_ansi_por_nivel():
    log, out = make(color="on")
    for method in ("debug", "info", "warning", "error"):
        getattr(log, method)("m")
    colored = lines(out)
    assert all("\x1b[" in ln for ln in colored)
    assert len({re.search(r"\x1b\[[0-9;]*m(\w+) *\x1b\[0m", ln).group(0) for ln in colored}) == 4
    assert [ANSI.sub("", ln)[13:20].strip() for ln in colored] == ["DEBUG", "INFO", "WARNING", "ERROR"]


def test_cor_off_sem_ansi():
    log, out = make(color="off")
    log.error("m", a=1)
    assert "\x1b" not in out.getvalue()


def test_auto_sem_tty_sem_ansi():
    log, out = make(color="auto")
    log.info("m")
    assert "\x1b" not in out.getvalue()


def test_auto_com_tty_tem_ansi():
    log, out = make(FakeTTY(), color="auto")
    log.info("m")
    assert "\x1b[" in out.getvalue()


def test_auto_com_tty_e_no_color_sem_ansi():
    stream = FakeTTY()
    log = build_logger(LoggingSettings(color="auto"), stream, no_color=True)
    log.info("m")
    assert "\x1b" not in stream.getvalue()


def test_no_color_do_ambiente_e_respeitado(monkeypatch):
    monkeypatch.setenv("NO_COLOR", "1")
    stream = FakeTTY()
    build_logger(LoggingSettings(color="auto"), stream).info("m")
    assert "\x1b" not in stream.getvalue()
    monkeypatch.delenv("NO_COLOR")
    stream2 = FakeTTY()
    build_logger(LoggingSettings(color="auto"), stream2).info("m")
    assert "\x1b[" in stream2.getvalue()


def test_cor_on_vence_no_color():
    stream = io.StringIO()
    build_logger(LoggingSettings(color="on"), stream, no_color=True).info("m")
    assert "\x1b[" in stream.getvalue()


# --- bind ------------------------------------------------------------------------
def test_bind_acrescenta_campos_sem_alterar_o_original():
    log, out = make(format="json")
    child = log.bind(correlation_id="c-1")
    child.info("a")
    log.info("b")
    first, second = (json.loads(ln) for ln in lines(out))
    assert first["correlation_id"] == "c-1"
    assert "correlation_id" not in second
    assert child.bind(extra=1) is not child


def test_campo_do_evento_vence_o_bind():
    log, out = make(format="json")
    log.bind(a=1).info("x", a=2)
    assert json.loads(lines(out)[0])["a"] == 2


# --- truncamento e lentidão ---------------------------------------------------------
def test_trunca_por_max_field_chars():
    log, out = make(max_field_chars=30)
    log.info("x", valor="z" * 200)
    assert "z" * 31 not in out.getvalue()
    assert "[+170 chars]" in out.getvalue()


def test_operacao_lenta_vira_aviso_e_marcacao():
    log, out = make(level="INFO", slow_ms=100, format="json")
    log.info("select", duration_ms=250)
    data = json.loads(lines(out)[0])
    assert data["level"] == "WARNING" and data["slow"] is True


def test_operacao_rapida_ou_no_limite_nao_e_marcada():
    log, out = make(slow_ms=100, format="json")
    log.info("a", duration_ms=100)
    log.info("b", duration_ms=5)
    for ln in lines(out):
        data = json.loads(ln)
        assert data["level"] == "INFO" and "slow" not in data


def test_slow_ms_zero_desliga_destaque():
    log, out = make(slow_ms=0, format="json")
    log.info("a", duration_ms=10**6)
    assert json.loads(lines(out)[0])["level"] == "INFO"


def test_lentidao_respeita_filtro_de_nivel_e_nao_rebaixa_erro():
    log, out = make(level="WARNING", slow_ms=100, format="json")
    log.info("rapida", duration_ms=1)
    log.info("lenta", duration_ms=500)
    log.error("erro lento", duration_ms=500)
    levels = [json.loads(ln)["level"] for ln in lines(out)]
    assert levels == ["WARNING", "ERROR"]


def test_slow_destacado_em_pretty_com_cor():
    log, out = make(color="on", slow_ms=10)
    log.info("x", duration_ms=50)
    assert "\x1b[1;33mtrue" in out.getvalue()


def test_duration_bool_nao_conta():
    log, out = make(slow_ms=1, format="json")
    log.info("x", duration_ms=True)
    assert json.loads(lines(out)[0])["level"] == "INFO"


# --- segredos ----------------------------------------------------------------------
@pytest.mark.parametrize("fmt", ["pretty", "json"])
@pytest.mark.parametrize("color", ["off", "on"])
def test_segredo_plantado_nunca_aparece(fmt, color):
    log, out = make(format=fmt, color=color)
    log.error(
        f"falha com {SB_SECRET}",
        headers={"Authorization": f"Bearer {JWT}", "apikey": SB_SECRET},
        url=f"https://x.supabase.co/storage/v1/object/sign/b/f.pdf?token={JWT}",
        chave=Secret("valor-secreto-123"),
        erro=RuntimeError(f"boom {JWT}"),
        conn="postgresql://u:senha-plantada@h/db",
    )
    text = out.getvalue()
    for planted in (SB_SECRET, JWT, "valor-secreto-123", "senha-plantada"):
        assert planted not in text


def test_extra_secrets_sao_mascarados():
    stream = io.StringIO()
    log = build_logger(LoggingSettings(color="off"), stream, extra_secrets=[Secret("minha-chave-xyz")])
    log.info("usando minha-chave-xyz", campo="minha-chave-xyz")
    assert "minha-chave-xyz" not in stream.getvalue()


def test_bind_tambem_e_sanitizado():
    log, out = make()
    log.bind(token="abc-def-ghi").info("x")
    assert "abc-def-ghi" not in out.getvalue()


# --- saída ------------------------------------------------------------------------
def test_stream_padrao_e_stderr(capsys):
    build_logger(LoggingSettings(color="off", level="INFO")).info("para stderr")
    captured = capsys.readouterr()
    assert captured.out == "" and "para stderr" in captured.err


def test_falha_de_stream_nao_levanta():
    class Quebrado:
        def write(self, _):
            raise OSError("disco cheio")

    log = StructuredLogger(LoggingSettings(), stream=Quebrado())
    log.error("nao deve levantar")


def test_is_enabled():
    log, _ = make(level="WARNING")
    assert not log.is_enabled("info") and log.is_enabled("ERROR")


def test_nao_configura_logging_global():
    import logging as stdlib_logging

    before = list(stdlib_logging.getLogger().handlers)
    make()[0].info("x")
    assert stdlib_logging.getLogger().handlers == before
