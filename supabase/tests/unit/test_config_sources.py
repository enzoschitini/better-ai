"""Fontes de configuração: ambiente, .env, dict, encadeada e fallback legado."""
from __future__ import annotations

from bai_supabase.config import (
    ChainedSource,
    DictSource,
    DotenvFileSource,
    EnvironmentSource,
    LegacyFallbackSource,
    SettingsSource,
)
from bai_supabase.config.sources import no_color_requested, parse_dotenv
from tests.fakes.logger import CaptureLogger

LEGACY_SECRET = "legacy-valor-plantado-123"


def test_todas_cumprem_o_protocolo():
    for source in (DictSource(), EnvironmentSource({}), DotenvFileSource("nao-existe.env"),
                   ChainedSource(DictSource()), LegacyFallbackSource(DictSource())):
        assert isinstance(source, SettingsSource)


def test_dict_source_ignora_nao_str():
    src = DictSource({"A": "1", "B": 2})  # type: ignore[dict-item]
    assert src.get("A") == "1" and src.get("B") is None and src.get("C") is None
    assert list(src.names()) == ["A"]


def test_environment_source_injetada_e_real(monkeypatch):
    assert EnvironmentSource({"X": "1"}).get("X") == "1"
    monkeypatch.setenv("SBX_FOO_TESTE", "v")
    real = EnvironmentSource()
    assert real.get("SBX_FOO_TESTE") == "v"
    assert "SBX_FOO_TESTE" in real.names()


def test_parse_dotenv():
    text = "\n".join([
        "# comentario", "", "A=1", "export B=dois", 'C="com espaco # nao e comentario"', "D='x y'",
        "E=valor # comentario inline", "F=", "  G = 7 ", "1X=ignorada", "sem igual", "H=a=b",
    ])
    assert parse_dotenv(text) == {
        "A": "1", "B": "dois", "C": "com espaco # nao e comentario", "D": "x y",
        "E": "valor", "F": "", "G": "7", "H": "a=b",
    }


def test_dotenv_so_le_quando_pedido(tmp_path, monkeypatch):
    path = tmp_path / ".env"
    path.write_text("SBX_URL=https://x\n", encoding="utf-8")
    reads = []
    original = type(path).read_text
    monkeypatch.setattr(type(path), "read_text", lambda self, *a, **k: reads.append(1) or original(self, *a, **k))
    src = DotenvFileSource(path)
    assert reads == []  # construir não lê
    assert src.get("SBX_URL") == "https://x"
    assert src.get("OUTRA") is None
    assert len(reads) == 1  # cache
    assert src.reads_files is True


def test_dotenv_arquivo_inexistente_e_vazio(tmp_path):
    src = DotenvFileSource(tmp_path / "nada.env")
    assert src.get("A") is None and list(src.names()) == []


def test_chained_primeira_com_valor_vence_e_vazio_nao_vence():
    chain = ChainedSource(DictSource({"A": "  ", "B": "env"}), DictSource({"A": "arq", "B": "arq", "C": "c"}))
    assert chain.get("A") == "arq" and chain.get("B") == "env" and chain.get("C") == "c"
    assert chain.get("Z") is None
    assert sorted(chain.names()) == ["A", "B", "C"]


def test_chained_reads_files_propaga():
    assert ChainedSource(DictSource(), DotenvFileSource("x")).reads_files is True
    assert ChainedSource(DictSource()).reads_files is False


def test_fallback_desligado_por_padrao():
    src = LegacyFallbackSource(DictSource({"SUPABASE_URL": "https://legado"}))
    assert src.get("SBX_URL") is None
    assert src.legacy_names_used == ()


def test_fallback_ligado_por_parametro_so_para_nomes_mapeados():
    log = CaptureLogger()
    inner = DictSource({"SUPABASE_URL": "https://legado", "SUPABASE_SECRET_KEY": LEGACY_SECRET, "SUPABASE_OUTRA": "x"})
    src = LegacyFallbackSource(inner, enabled=True, logger=log)
    assert src.get("SBX_URL") == "https://legado"
    assert src.get("SBX_SECRET_KEY") == LEGACY_SECRET
    assert src.get("SBX_OUTRA") is None
    assert src.legacy_names_used == ("SBX_URL", "SBX_SECRET_KEY")
    # só nomes no log
    assert [e[1] for e in log.events] == ["fallback legado de configuração usado"] * 2
    assert LEGACY_SECRET not in repr(log.events) and "https://legado" not in repr(log.events)
    assert log.events[0][2] == {"variable": "SBX_URL", "legacy_variable": "SUPABASE_URL"}


def test_fallback_ligado_pela_variavel():
    inner = DictSource({"SBX_ALLOW_LEGACY_FALLBACK": "yes", "SUPABASE_URL": "https://legado"})
    assert LegacyFallbackSource(inner).get("SBX_URL") == "https://legado"


def test_fallback_nome_novo_tem_prioridade():
    inner = DictSource({"SBX_URL": "https://novo", "SUPABASE_URL": "https://legado"})
    src = LegacyFallbackSource(inner, enabled=True)
    assert src.get("SBX_URL") == "https://novo"
    assert src.legacy_names_used == ()


def test_fallback_logado_so_uma_vez():
    log = CaptureLogger()
    src = LegacyFallbackSource(DictSource({"SUPABASE_URL": "https://l"}), enabled=True, logger=log)
    src.get("SBX_URL")
    src.get("SBX_URL")
    assert len(log.events) == 1


def test_no_color_requested():
    assert no_color_requested({"NO_COLOR": "1"}) is True
    assert no_color_requested({"NO_COLOR": ""}) is False
    assert no_color_requested({}) is False
