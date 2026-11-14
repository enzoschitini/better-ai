"""Serialização dict <-> entidade (T-201)."""
from __future__ import annotations

import dataclasses
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

import pytest

from bai_supabase.contracts.tables import TableDescriptor
from bai_supabase.errors.exceptions import ConfigurationError, MappingError, ValidationError
from bai_supabase.tables.serialization import EntityCodec, entity_kind, to_wire_value

UTC = timezone.utc


class Color(Enum):
    RED = "red"


@dataclasses.dataclass
class Doc:
    id: Optional[UUID] = None
    title: str = ""
    price: Decimal = Decimal("0")
    created_at: Optional[datetime] = None
    day: Optional[date] = None
    color: Optional[Color] = None
    tags: list[str] = dataclasses.field(default_factory=list)
    meta: dict = dataclasses.field(default_factory=dict)


def wire(v, field="f"):
    return to_wire_value(v, table="t", field=field)


def test_wire_types():
    u = uuid4()
    assert wire(u) == str(u)
    assert wire(Decimal("12.50")) == "12.50"
    assert wire(Color.RED) == "red"
    assert wire(date(2024, 1, 2)) == "2024-01-02"
    assert wire({"a": [1, {"b": u}]}) == {"a": [1, {"b": str(u)}]}
    assert wire({3, 1, 2}) == [1, 2, 3]


def test_wire_datetime_converte_para_utc():
    dt = datetime(2024, 1, 1, 12, tzinfo=timezone(timedelta(hours=2)))
    assert wire(dt) == "2024-01-01T10:00:00+00:00"


def test_datetime_ingenuo_recusado_sem_vazar_valor():
    with pytest.raises(ValidationError) as exc:
        wire(datetime(2024, 1, 1, 12, 30), field="created_at")
    assert "created_at" in str(exc.value) and "'t'" in str(exc.value)
    assert "2024" not in str(exc.value)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), Decimal("NaN")])
def test_numero_nao_finito_recusado(bad):
    with pytest.raises(ValidationError):
        wire(bad)


def test_tipo_nao_suportado_cita_campo_nao_valor():
    with pytest.raises(MappingError) as exc:
        wire(object(), field="payload")
    assert "payload" in str(exc.value)
    with pytest.raises(MappingError):
        wire({1: "x"})


def test_entity_kind():
    assert entity_kind(None) == "dict"
    assert entity_kind(Doc) == "dataclass"

    class P:
        model_validate = model_dump = staticmethod(lambda *a, **k: None)

    assert entity_kind(P) == "pydantic"
    with pytest.raises(ConfigurationError):
        entity_kind(int)


def test_encode_insert_remove_gerenciadas_vazias_e_recusa_preenchidas():
    d = TableDescriptor("docs", server_managed_columns=("id", "created_at"))
    codec = EntityCodec(d)
    assert codec.encode_insert({"id": None, "title": "a", "created_at": None}) == {"title": "a"}
    with pytest.raises(ValidationError) as exc:
        codec.encode_insert({"id": "x", "title": "a"})
    assert "'id'" in str(exc.value) and "'docs'" in str(exc.value)
    # PK permitida no upsert
    assert codec.encode_insert({"id": "x"}, allowed_managed=("id",)) == {"id": "x"}


def test_encode_changes_recusa_pk_e_gerenciadas():
    codec = EntityCodec(TableDescriptor("docs", server_managed_columns=("created_at",)))
    assert codec.encode_changes({"title": None}) == {"title": None}  # None explícito grava NULL
    for col in ("id", "created_at"):
        with pytest.raises(ValidationError):
            codec.encode_changes({col: 1})


def test_dict_roundtrip():
    codec = EntityCodec(TableDescriptor("docs"))
    row = {"id": "1", "extra": True}
    out = codec.decode(row)
    assert out == row and out is not row
    assert codec.to_mapping({"a": 1}) == {"a": 1}
    with pytest.raises(MappingError):
        codec.decode("não é linha")


def test_dataclass_decode_converte_tipos_e_tolera_extras():
    codec = EntityCodec(TableDescriptor("docs", model=Doc))
    u = uuid4()
    doc = codec.decode({
        "id": str(u), "title": "t", "price": 12.5, "created_at": "2024-01-01T10:00:00+02:00",
        "day": "2024-03-04", "color": "red", "tags": ["a"], "meta": {"k": 1}, "coluna_nova": 1,
    })
    assert doc.id == u and doc.price == Decimal("12.5")
    assert doc.created_at == datetime(2024, 1, 1, 8, tzinfo=UTC)
    assert doc.day == date(2024, 3, 4) and doc.color is Color.RED and doc.tags == ["a"]


def test_dataclass_decode_erros_citam_campo_sem_valor():
    codec = EntityCodec(TableDescriptor("docs", model=Doc))
    with pytest.raises(MappingError) as exc:
        codec.decode({"id": "segredo-nao-uuid"})
    assert "id" in str(exc.value) and "segredo" not in str(exc.value)
    with pytest.raises(MappingError):
        codec.decode({"color": "azul"})

    @dataclasses.dataclass
    class Req:
        name: str

    with pytest.raises(MappingError) as exc2:
        EntityCodec(TableDescriptor("r", model=Req)).decode({})
    assert "name" in str(exc2.value)


def test_dataclass_to_mapping_e_tipo_incompativel():
    codec = EntityCodec(TableDescriptor("docs", model=Doc))
    assert codec.to_mapping(Doc(title="x"))["title"] == "x"
    with pytest.raises(ValidationError):
        codec.to_mapping(object())


def test_pydantic_real_e_mapping_error_sem_valor():
    pydantic = pytest.importorskip("pydantic")

    class Item(pydantic.BaseModel):
        id: Optional[UUID] = None
        qty: int

    codec = EntityCodec(TableDescriptor("items", model=Item))
    assert codec.kind == "pydantic"
    item = codec.decode({"id": str(uuid4()), "qty": 3, "x": 1})
    assert item.qty == 3
    assert codec.to_mapping(item)["qty"] == 3
    with pytest.raises(MappingError) as exc:
        codec.decode({"qty": "valor-secreto"})
    assert "qty" in str(exc.value) and "secreto" not in str(exc.value)
    assert codec.to_changes_mapping(Item(qty=1)) == {"qty": 1}
