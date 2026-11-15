"""Classe de tabelas: registro de descritores e Open/Closed (T-204)."""
from __future__ import annotations

import pytest

from src.database.supabase_integration.contracts.settings import TablesSettings
from src.database.supabase_integration.contracts.tables import TableDescriptor, TablesContract
from src.database.supabase_integration.errors.exceptions import ConfigurationError
from src.database.supabase_integration.tables import PostgresTableRepository, SupabaseTables
from src.database.supabase_integration.tests.fakes.executor import PassThroughExecutor
from src.database.supabase_integration.tests.fakes.logger import CaptureLogger
from src.database.supabase_integration.tests.fakes.table_transport import InMemoryTableTransport


def make(settings=None, **kw):
    return SupabaseTables(InMemoryTableTransport(), PassThroughExecutor(), CaptureLogger(), settings or TablesSettings(), **kw)


def test_implementa_o_contrato_e_entrega_repositorio_cacheado():
    tables = make()
    assert isinstance(tables, TablesContract)
    tables.register(TableDescriptor("docs"))
    repo = tables.table("docs")
    assert isinstance(repo, PostgresTableRepository) and tables.table("docs") is repo
    assert tables.registered() == ("docs",)


def test_nova_tabela_e_so_novo_descritor():
    tables = make()
    tables.register(TableDescriptor("a"))
    tables.register(TableDescriptor("b", primary_key="uid"))
    tables.table("a").insert({"x": 1})
    assert tables.table("b").descriptor.primary_key == "uid"


def test_tabela_nao_registrada_ou_nao_permitida():
    tables = make(TablesSettings(allowlist=("docs",)))
    with pytest.raises(ConfigurationError):
        tables.table("docs")  # permitida, mas não registrada
    with pytest.raises(ConfigurationError):
        tables.register(TableDescriptor("outra"))
    with pytest.raises(ConfigurationError):
        tables.table("segredos; drop")


def test_registro_duplicado():
    tables = make()
    tables.register(TableDescriptor("docs"))
    tables.register(TableDescriptor("docs"))  # idêntico: no-op
    with pytest.raises(ConfigurationError):
        tables.register(TableDescriptor("docs", primary_key="uid"))


def test_descritor_invalido_falha_no_registro():
    with pytest.raises(ConfigurationError):
        make().register(TableDescriptor("a b"))


def test_descritores_no_construtor_e_fabrica_injetada():
    created = []

    def factory(d):
        created.append(d.name)
        return object()

    tables = make(descriptors=[TableDescriptor("a"), TableDescriptor("b")], repository_factory=factory)
    tables.table("a"); tables.table("a")
    assert created == ["a"] and tables.registered() == ("a", "b")
