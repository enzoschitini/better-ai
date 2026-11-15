"""Tipo ``Secret``: valor sensível que nunca aparece em repr/str/log (research/05 §3.2)."""

from __future__ import annotations


class Secret:
    """Envolve um segredo. ``reveal()`` é o ÚNICO modo de ler o valor."""

    __slots__ = ("_value",)

    def __init__(self, value: str) -> None:
        object.__setattr__(self, "_value", value)

    def __setattr__(self, name, value):  # imutável
        raise AttributeError("Secret é imutável")

    def reveal(self) -> str:
        return self._value

    def __repr__(self) -> str:
        return "Secret('***')"

    __str__ = __repr__

    def __bool__(self) -> bool:
        return bool(self._value)

    def __eq__(self, other) -> bool:
        return isinstance(other, Secret) and self._value == other._value

    def __hash__(self) -> int:
        return hash(self._value)

    def __reduce__(self):
        raise TypeError("Secret não pode ser serializado")
