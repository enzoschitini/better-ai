"""Adapter de tabelas sobre um cliente SDK FALSO que registra a cadeia fluente (T-203)."""
from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from src.database.supabase_integration.adapters.tables_transport import SupabaseTableTransport
from src.database.supabase_integration.contracts.query import Condition, FilterGroup, Op, Sort
from src.database.supabase_integration.contracts.transports import SelectRequest, TableTransport
from src.database.supabase_integration.errors.exceptions import SupabaseIntegrationError, ValidationError


class FakeBuilder:
    """Imita a cadeia do postgrest-py e registra cada chamada em ``calls``."""

    def __init__(self, calls: list, data: Any = None, count: Any = None, error: Exception = None) -> None:
        self.calls, self._data, self._count, self._error = calls, data if data is not None else [], count, error

    def _rec(self, name, *args, **kwargs):
        self.calls.append((name, args, kwargs))
        return self

    def __getattr__(self, name):
        if name.startswith("_"):
            raise AttributeError(name)
        return lambda *a, **k: self._rec(name, *a, **k)

    @property
    def not_(self):
        return self._rec("not_")

    def execute(self):
        self.calls.append(("execute", (), {}))
        if self._error:
            raise self._error
        return SimpleNamespace(data=self._data, count=self._count)


class FakeClient:
    def __init__(self, **builder_kw) -> None:
        self.calls: list = []
        self._kw = builder_kw

    def _builder(self):
        return FakeBuilder(self.calls, **self._kw)

    def from_(self, table):
        self.calls.append(("from_", (table,), {}))
        return self._builder()

    def schema(self, schema):
        self.calls.append(("schema", (schema,), {}))
        return self


def transport(**kw):
    client = FakeClient(**kw)
    return SupabaseTableTransport(lambda: client), client


def names(client):
    return [c[0] for c in client.calls]


def test_cumpre_o_contrato_de_transporte():
    assert isinstance(transport()[0], TableTransport)


def test_select_traduz_colunas_filtros_ordem_range_e_count():
    t, c = transport(data=[{"id": 1}], count=42)
    req = SelectRequest(
        "docs", columns=("id", "n"), limit=10, offset=20, count="exact",
        filter=FilterGroup(items=(Condition("n", Op.GTE, 3), Condition("t", Op.IS_NULL), Condition("u", Op.NOT_NULL))),
        sorts=(Sort("n", descending=True, nulls_first=False), Sort("id")),
    )
    resp = t.select(req)
    assert resp.rows == [{"id": 1}] and resp.count == 42
    assert c.calls == [
        ("from_", ("docs",), {}),
        ("select", ("id,n",), {"count": "exact"}),
        ("gte", ("n", "3"), {}),
        ("is_", ("t", None), {}),
        ("not_", (), {}),
        ("is_", ("u", None), {}),
        ("order", ("n",), {"desc": True, "nullsfirst": False}),
        ("order", ("id",), {"desc": False, "nullsfirst": None}),
        ("range", (20, 29), {}),
        ("execute", (), {}),
    ]


def test_select_sem_colunas_sem_limite_e_so_offset():
    t, c = transport()
    t.select(SelectRequest("docs"))
    assert ("select", ("*",), {"count": None}) in c.calls and "range" not in names(c)
    t.select(SelectRequest("docs", offset=5))
    assert ("offset", (5,), {}) in c.calls


def test_schema_diferente_do_padrao_usa_client_schema():
    t, c = transport()
    t.select(SelectRequest("docs", schema="app"))
    assert c.calls[:2] == [("schema", ("app",), {}), ("from_", ("docs",), {})]
    c.calls.clear()
    t.select(SelectRequest("docs", schema="public"))
    assert "schema" not in names(c)
    custom = SupabaseTableTransport(lambda: c, default_schema="app")
    c.calls.clear()
    custom.select(SelectRequest("docs", schema="public"))
    assert names(c)[0] == "schema"


@pytest.mark.parametrize("cond,expected", [
    (Condition("a", Op.EQ, True), ("eq", ("a", "true"))),
    (Condition("a", Op.NEQ, 1), ("neq", ("a", "1"))),
    (Condition("a", Op.GT, 1.5), ("gt", ("a", "1.5"))),
    (Condition("a", Op.LT, "x"), ("lt", ("a", "x"))),
    (Condition("a", Op.LTE, "x"), ("lte", ("a", "x"))),
    (Condition("a", Op.LIKE, "a%"), ("like", ("a", "a%"))),
    (Condition("a", Op.ILIKE, "a%"), ("ilike", ("a", "a%"))),
    (Condition("a", Op.IN, ["x", "y,z", 'q"r']), ("filter", ("a", "in", '(x,"y,z","q\\"r")'))),
    (Condition("a", Op.IN, []), ("filter", ("a", "in", "()"))),
    (Condition("a", Op.CONTAINS, ["x", "y z"]), ("contains", ("a", '{x,"y z"}'))),
    (Condition("a", Op.CONTAINS, {"k": 1}), ("contains", ("a", '{"k":1}'))),
])
def test_todos_os_operadores_usam_parametros_do_sdk(cond, expected):
    t, c = transport()
    t.select(SelectRequest("docs", filter=cond))
    assert (expected[0], expected[1], {}) in c.calls


def test_valor_malicioso_vai_como_parametro_nunca_concatenado():
    t, c = transport()
    evil = "x&select=*&or=(id.gt.0)"
    t.select(SelectRequest("docs", filter=Condition("a", Op.EQ, evil)))
    assert ("eq", ("a", evil), {}) in c.calls  # valor intacto num único argumento
    assert not any(n == "or_" for n in names(c))


def test_or_aninhado_com_escape():
    t, c = transport()
    flt = FilterGroup(logic="and", items=(
        Condition("s", Op.EQ, "ativo"),
        FilterGroup(logic="or", items=(
            Condition("n", Op.LT, 2),
            FilterGroup(logic="and", items=(Condition("t", Op.EQ, "a,b)"), Condition("u", Op.IS_NULL))),
            Condition("k", Op.IN, ["p", "q.r"]),
        )),
    ))
    t.select(SelectRequest("docs", filter=flt))
    assert ("eq", ("s", "ativo"), {}) in c.calls
    assert ("or_", ('n.lt.2,and(t.eq."a,b)",u.is.null),k.in.(p,"q.r")',), {}) in c.calls


def test_or_na_raiz_e_grupos_vazios_ignorados():
    t, c = transport()
    t.select(SelectRequest("docs", filter=FilterGroup(logic="or", items=(
        Condition("a", Op.EQ, 1), FilterGroup(), Condition("b", Op.NOT_NULL), Condition("c", Op.CONTAINS, ["x"]),
    ))))
    assert ("or_", ("a.eq.1,b.not.is.null,c.cs.{x}",), {}) in c.calls
    c.calls.clear()
    t.select(SelectRequest("docs", filter=FilterGroup(logic="or", items=(Condition("a", Op.EQ, 1), FilterGroup()))))
    assert ("eq", ("a", "1"), {}) in c.calls and "or_" not in names(c)  # um único item: sem or


def test_keyset_dois_grupos_or_no_topo():
    t, c = transport()
    after = FilterGroup(logic="or", items=(
        Condition("n", Op.GT, 3),
        FilterGroup(logic="and", items=(Condition("n", Op.EQ, 3), Condition("id", Op.GT, "a-b"))),
    ))
    t.select(SelectRequest("docs", filter=FilterGroup(logic="and", items=(after,))))
    assert ("or_", ("n.gt.3,and(n.eq.3,id.gt.a-b)",), {}) in c.calls


def test_insert_upsert_update_delete():
    t, c = transport(data=[{"id": 1}])
    assert t.insert("docs", "public", [{"a": 1}]) == [{"id": 1}]
    assert c.calls[1] == ("insert", ([{"a": 1}],), {"default_to_null": False})
    c.calls.clear()
    t.upsert("docs", "public", [{"a": 1}], on_conflict="a,b", ignore_duplicates=True)
    assert c.calls[1] == ("upsert", ([{"a": 1}],), {"on_conflict": "a,b", "ignore_duplicates": True, "default_to_null": False})
    c.calls.clear()
    t.upsert("docs", "public", [{"a": 1}])
    assert c.calls[1][2]["on_conflict"] == ""
    c.calls.clear()
    assert t.update("docs", "public", {"a": 2}, Condition("id", Op.EQ, "7")) == [{"id": 1}]
    assert [n for n in names(c)] == ["from_", "update", "eq", "execute"]
    c.calls.clear()
    t.delete("docs", "public", Condition("id", Op.EQ, "7"))
    assert names(c) == ["from_", "delete", "eq", "execute"]


def test_update_e_delete_sem_filtro_nunca_chegam_ao_sdk():
    t, c = transport()
    for empty in (None, FilterGroup(), FilterGroup(items=(FilterGroup(),))):
        with pytest.raises(ValidationError):
            t.update("docs", "public", {"a": 1}, empty)
        with pytest.raises(ValidationError):
            t.delete("docs", "public", empty)
    assert c.calls == []


def test_excecao_do_sdk_vira_erro_de_dominio_com_causa():
    boom = RuntimeError("detalhe do SDK com valor-secreto")
    t, _ = transport(error=boom)
    with pytest.raises(SupabaseIntegrationError) as exc:
        t.select(SelectRequest("docs"))
    assert exc.value.__cause__ is boom and "valor-secreto" not in str(exc.value)
    for call in (
        lambda: t.insert("docs", "public", [{}]),
        lambda: t.upsert("docs", "public", [{}]),
        lambda: t.update("docs", "public", {}, Condition("a", Op.EQ, 1)),
        lambda: t.delete("docs", "public", Condition("a", Op.EQ, 1)),
    ):
        with pytest.raises(SupabaseIntegrationError):
            call()


def test_resposta_nao_lista_e_erro_e_none_vira_vazio():
    t, _ = transport(data="texto")
    with pytest.raises(SupabaseIntegrationError):
        t.insert("docs", "public", [{}])
    t2, c2 = transport()
    c2._kw["data"] = None
    assert t2.delete("docs", "public", Condition("a", Op.EQ, 1)) == []


def test_valor_de_filtro_nao_suportado_e_validation_error():
    t, _ = transport()
    with pytest.raises(SupabaseIntegrationError):
        t.select(SelectRequest("docs", filter=Condition("a", Op.EQ, object())))


def test_provedor_e_chamado_a_cada_operacao():
    clients = []

    def provider():
        clients.append(FakeClient())
        return clients[-1]

    t = SupabaseTableTransport(provider)
    t.select(SelectRequest("docs"))
    t.select(SelectRequest("docs"))
    assert len(clients) == 2


def test_modulo_nao_importa_o_sdk():
    import ast
    import src.database.supabase_integration.adapters.tables_transport as mod

    tree = ast.parse(open(mod.__file__, encoding="utf-8").read())
    imported = {n.names[0].name.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.Import)}
    imported |= {n.module.split(".")[0] for n in ast.walk(tree) if isinstance(n, ast.ImportFrom) and n.module}
    assert not imported & {"supabase", "postgrest", "storage3", "httpx"}
