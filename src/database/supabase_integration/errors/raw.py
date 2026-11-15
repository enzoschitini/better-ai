"""Erro bruto normalizado (research/02 §5.1).

O adapter converte qualquer exceção do SDK/transporte neste registro; o mapeador
(``errors.mapper``) o converte para a hierarquia do domínio. Sem dependência do SDK.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Optional

Origin = Literal["table", "storage", "transport"]


@dataclass(frozen=True)
class RawError:
    origin: Origin
    status: Optional[int] = None
    code: Optional[str] = None
    message: Optional[str] = None
    details: Optional[str] = None
    hint: Optional[str] = None
    retry_after: Optional[float] = None
    #: Para transporte: "timeout" | "connect" | "decode" | "other".
    transport_kind: Optional[str] = None
    #: Nome do tipo da exceção original (informativo; não usado para decidir).
    exception_type: Optional[str] = None
