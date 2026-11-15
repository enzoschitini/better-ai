"""Validação de entrada da frente A (T-202)."""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest

from bai_supabase.contracts.query import Condition, FilterGroup, Op, Query, Sort
from bai_supabase.contracts.settings import TablesSettings
from bai_supabase.contracts.tables import BatchOptions, TableDescriptor
from bai_supabase.errors.exceptions import ConfigurationError, SupabaseIntegrationError, ValidationError
from bai_supabase.tables.validation import TableValidator, ensure_table_allowed, validate_descriptor, validate_identifier


def make(columns=None, **kw):
    return TableValidator(TableDescriptor("docs", columns=columns, **kw), TablesSettings())


@pytest.mark.parametrize("name", ["docs", "_x", "Col9", "a" * 63])
def test_identificador_valido(name):
    assert validate_identifier(name) == name


@pytest.mark.parametrize("name", ["", "9a", "a-b", "a;drop table x", "a b", "a" * 64, None, 5, "a.b"])
def test_identificador_invalido(name):
    with pytest.raises(ValidationError):
        validate_identifier(name, "coluna")


def test_mensagem_trunca_e_escapa_nome_malicioso():
    with pytest.raises(ValidationError) as exc:
        validate_identifier("x;" + "A" * 200 + "\n<script>", "coluna")
    assert len(str(exc.value)) < 100 and "\n" not in str(exc.value)


def test_allowlist_de_tabelas():
    ensure_table_allowed("a", ())  # vazio = qualquer
    ensure_table_allowed("a", ("a", "b"))
    with pytest.raises(ConfigurationError):
        ensure_table_allowed("c", ("a", "b"))


def test_validate_descriptor():
    validate_descriptor(TableDescriptor("docs", columns=("id", "t"), sort_key="id"))
    for bad in (
        TableDescriptor("bad name"),
        TableDescriptor("docs", schema="a-b"),
        TableDescriptor("docs", columns=()),
        TableDescriptor("docs", columns=("t",)),  # PK fora da allowlist
        TableDescriptor("docs", columns=("id",), sort_key="created"),
        TableDescriptor("docs", model=int),
    ):
        with pytest.raises(ConfigurationError):
            validate_descriptor(bad)
    with pytest.raises(ConfigurationError):
        validate_descriptor(TableDescriptor("docs"), ("outra",))


def test_coluna_fora_da_allowlist_recusada_em_filtro_ordem_e_select():
    v = make(columns=("id", "title"))
    for q in (
        Query.eq("senha", 1),
        Query(sorts=(Sort("senha"),)),
        Query(columns=("senha",)),
    ):
        with pytest.raises(ValidationError):
            v.query(q)
    assert v.query(Query.eq("title", "x")).columns == ("id", "title")  # nunca "*" com allowlist


def test_sem_allowlist_select_e_estrela():
    assert make().query(Query()).columns is None


def test_operador_desconhecido_e_valores():
    v = make()
    with pytest.raises(ValidationError):
        v.filter(Condition("a", "drop", 1))  # type: ignore[arg-type]
    assert v.filter(Condition("a", "eq", 1)).op is Op.EQ  # str do enum é aceita
    bad = [
        Condition("a", Op.EQ, None), Condition("a", Op.EQ, [1]), Condition("a", Op.IN, "abc"),
        Condition("a", Op.IN, [None]), Condition("a", Op.LIKE, 3), Condition("a", Op.CONTAINS, 3),
        Condition("a", Op.IN, list(range(1001))),
    ]
    for c in bad:
        with pytest.raises(ValidationError):
            v.filter(c)


def test_valores_de_filtro_viram_wire_e_datetime_exige_fuso():
    v = make()
    u = uuid4()
    assert v.filter(Condition("id", Op.EQ, u)).value == str(u)
    assert v.filter(Condition("id", Op.IN, [u])).value == [str(u)]
    assert v.filter(Condition("a", Op.IS_NULL, "ignorado")).value is None
    ok = datetime(2024, 1, 1, tzinfo=timezone.utc)
    assert v.filter(Condition("t", Op.GTE, ok)).value == "2024-01-01T00:00:00+00:00"
    with pytest.raises(ValidationError):
        v.filter(Condition("t", Op.GTE, datetime(2024, 1, 1)))


def test_grupo_invalido_e_profundidade():
    v = make()
    with pytest.raises(ValidationError):
        v.filter(FilterGroup(items=(Condition("a", Op.EQ, 1),), logic="xor"))
    node = Condition("a", Op.EQ, 1)
    for _ in range(12):
        node = FilterGroup(items=(node,))
    with pytest.raises(ValidationError):
        v.filter(node)


def test_filtro_vazio_recusado_em_massa():
    v = make()
    for empty in (None, FilterGroup(), FilterGroup(items=(FilterGroup(),))):
        with pytest.raises(ValidationError) as exc:
            v.non_empty_filter(empty, "delete_where")
        assert "filtro vazio" in str(exc.value)
    assert v.non_empty_filter(Condition("a", Op.EQ, 1), "delete_where")


def test_colunas_de_escrita_e_conflito():
    v = make(columns=("id", "title"))
    v.write_columns(["title"])
    with pytest.raises(ValidationError):
        v.write_columns(["title", "is_admin"])
    assert v.conflict_columns(None) == ("id",)
    assert v.conflict_columns("id, title") == ("id", "title")
    for bad in ("", "x", "id;"):
        with pytest.raises(ValidationError):
            v.conflict_columns(bad)


def test_record_id():
    v = make()
    u = uuid4()
    assert v.record_id(u) == str(u) and v.record_id(5) == 5 and v.record_id("a") == "a"
    for bad in (None, True, 1.5, "", "  ", object()):
        with pytest.raises(SupabaseIntegrationError):
            v.record_id(bad)


def test_lote_vazio_e_opcoes():
    v = make()
    with pytest.raises(ValidationError):
        v.non_empty_batch([], "insert_many")
    assert v.batch_options(None) == (500, "continue")
    assert v.batch_options(BatchOptions(batch_size=10, mode="stop")) == (10, "stop")
    for bad in (BatchOptions(batch_size=0), BatchOptions(batch_size=1001), BatchOptions(mode="x"), BatchOptions(batch_size=True)):
        with pytest.raises(ValidationError):
            v.batch_options(bad)


def test_offset():
    v = make()
    assert v.offset(0) == 0
    for bad in (-1, 1.5, True):
        with pytest.raises(ValidationError):
            v.offset(bad)
