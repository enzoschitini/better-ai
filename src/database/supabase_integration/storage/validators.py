"""Validação de entrada da classe de arquivos (research/07 §4-§6, research/05 §7).

Tudo aqui é função pura ou usa só ``StorageSettings``: falha ANTES de ir à rede (P5).
Erros usam a hierarquia do domínio (``ValidationError``, ``FileTooLargeError``,
``ConfigurationError``).
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Optional

import filetype

from bai_supabase.contracts.settings import StorageSettings
from bai_supabase.errors.exceptions import ConfigurationError, FileTooLargeError, ValidationError

#: Quantos bytes iniciais bastam para a detecção por conteúdo (magic bytes).
HEAD_BYTES = 8192

MAX_KEY_LENGTH = 1024  # limite de chave do Storage
MAX_SEGMENT_LENGTH = 255
MAX_PATH_DEPTH = 8
MAX_SLUG_LENGTH = 100
MAX_ORIGINAL_NAME_LENGTH = 255

_SEGMENT_RE = re.compile(r"^[A-Za-z0-9._-]+$")
_PERCENT_RE = re.compile(r"%[0-9A-Fa-f]{2}")
_BUCKET_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")
_EXT_RE = re.compile(r"^\.[a-z0-9]{1,10}$")
_WINDOWS_RESERVED = frozenset(
    {"con", "prn", "aux", "nul", "conin$", "conout$"}
    | {f"com{i}" for i in range(1, 10)}
    | {f"lpt{i}" for i in range(1, 10)}
)

GENERIC_MIME = "application/octet-stream"


def _short(value: str) -> str:
    """Trecho seguro para mensagens (repr escapa controles; truncado)."""
    return repr(value if len(value) <= 80 else value[:80] + "...")


def _is_control(ch: str) -> bool:
    return ord(ch) < 32 or ord(ch) == 127 or unicodedata.category(ch) in ("Cc", "Cf")


def _is_windows_reserved(segment: str) -> bool:
    return segment.split(".", 1)[0].rstrip(" ").lower() in _WINDOWS_RESERVED


# --- caminhos --------------------------------------------------------------------
def validate_object_path(path: str, *, max_depth: int = MAX_PATH_DEPTH) -> str:
    """Valida e normaliza (NFC) o caminho de um objeto; devolve o caminho seguro.

    Rejeita: vazio, controles/bytes nulos, ``\\``, ``/`` inicial, segmentos vazios, ``.``/``..``,
    segmentos que começam ou terminam com ponto, sequências ``%XX`` (codificação), unidade
    (``C:``), nomes reservados do Windows, caracteres fora de ``[A-Za-z0-9._-]``, e excesso de
    tamanho/profundidade.
    """
    if not isinstance(path, str) or not path:
        raise ValidationError("caminho do objeto vazio ou inválido", operation="storage.validate")
    path = unicodedata.normalize("NFC", path)
    if any(_is_control(c) for c in path):
        raise ValidationError("caminho contém caractere de controle ou byte nulo", operation="storage.validate")
    if "\\" in path:
        raise ValidationError("caminho não pode conter barra invertida", operation="storage.validate")
    if path.startswith("/"):
        raise ValidationError("caminho não pode ser absoluto (começar com '/')", operation="storage.validate")
    if _PERCENT_RE.search(path):
        raise ValidationError("caminho não pode conter sequência codificada (%XX)", operation="storage.validate")
    if re.match(r"^[A-Za-z]:", path):
        raise ValidationError("caminho não pode conter letra de unidade", operation="storage.validate")
    if len(path.encode("utf-8")) > MAX_KEY_LENGTH:
        raise ValidationError(f"caminho excede {MAX_KEY_LENGTH} bytes", operation="storage.validate")
    segments = path.split("/")
    if len(segments) > max_depth:
        raise ValidationError(f"caminho excede a profundidade máxima ({max_depth})", operation="storage.validate")
    for segment in segments:
        _validate_segment(segment, path)
    return path


def _validate_segment(segment: str, path: str) -> None:
    if segment == "":
        raise ValidationError("caminho com segmento vazio ('//' ou '/' final)", operation="storage.validate")
    if segment in (".", "..") or segment.startswith("."):
        raise ValidationError(
            f"segmento inválido em {_short(path)} (travessia ou nome oculto)", operation="storage.validate"
        )
    if segment.endswith((".", " ")):
        raise ValidationError("segmento não pode terminar com ponto ou espaço", operation="storage.validate")
    if len(segment) > MAX_SEGMENT_LENGTH:
        raise ValidationError(f"segmento excede {MAX_SEGMENT_LENGTH} caracteres", operation="storage.validate")
    if not _SEGMENT_RE.match(segment):
        raise ValidationError(
            f"caracteres não permitidos em {_short(path)} (use letras ASCII, números, '.', '_' e '-')",
            operation="storage.validate",
        )
    if _is_windows_reserved(segment):
        raise ValidationError("segmento usa nome reservado do Windows", operation="storage.validate")


def validate_prefix(prefix: Optional[str], *, allow_empty: bool = True, max_depth: int = MAX_PATH_DEPTH) -> str:
    """Valida um prefixo (pasta). Aceita uma barra final; devolve sem ela."""
    if prefix is None or prefix == "":
        if allow_empty:
            return ""
        raise ValidationError("prefixo vazio não é permitido nesta operação", operation="storage.validate")
    if prefix.endswith("/"):
        prefix = prefix[:-1]
    return validate_object_path(prefix, max_depth=max_depth)


# --- nomes -----------------------------------------------------------------------
def sanitize_original_name(name: Optional[str]) -> str:
    """Nome original saneado para METADADO (legível; nunca usado como caminho)."""
    if not name:
        return "arquivo"
    base = re.split(r"[\\/]", unicodedata.normalize("NFC", name))[-1]
    base = "".join(c for c in base if not _is_control(c)).strip(" .")
    if not base:
        return "arquivo"
    if len(base) > MAX_ORIGINAL_NAME_LENGTH:
        tail = base[len(base) - len(extension_of(base)):] if extension_of(base) else ""
        base = base[: MAX_ORIGINAL_NAME_LENGTH - len(tail)] + tail
    return base


def extension_of(filename: Optional[str]) -> str:
    """Extensão em minúsculas (``.mp4``) ou ``""`` se ausente/suspeita."""
    if not filename:
        return ""
    base = re.split(r"[\\/]", filename)[-1].lstrip(".")
    _, dot, ext = base.rpartition(".")
    candidate = f".{ext.lower()}" if dot else ""
    return candidate if _EXT_RE.match(candidate) else ""


def slugify_filename(name: Optional[str], *, max_length: int = MAX_SLUG_LENGTH) -> str:
    """Nome seguro para caminho: NFKD sem acentos, minúsculo, ``[a-z0-9._-]``, extensão preservada."""
    ext = extension_of(name)
    base = re.split(r"[\\/]", name or "")[-1].lstrip(".")
    stem = base[: len(base) - len(ext)] if ext else base
    stem = unicodedata.normalize("NFKD", stem).encode("ascii", "ignore").decode("ascii").lower()
    stem = re.sub(r"[^a-z0-9]+", "-", stem).strip("-") or "arquivo"
    if _is_windows_reserved(stem):
        stem = f"{stem}-arquivo"
    stem = stem[: max(1, max_length - len(ext))].strip("-") or "arquivo"
    return stem + ext


# --- bucket ----------------------------------------------------------------------
def resolve_bucket(bucket: Optional[str], settings: StorageSettings) -> str:
    """Resolve o bucket (``None`` = padrão) e valida contra a allowlist.

    ``ConfigurationError`` se não há bucket padrão/permitido configurado; ``ValidationError``
    se o bucket pedido tem formato inválido ou está fora da allowlist.
    """
    allowed = settings.buckets_allowlist or ((settings.default_bucket,) if settings.default_bucket else ())
    if bucket is None:
        if not settings.default_bucket:
            raise ConfigurationError("bucket padrão não configurado", operation="storage.validate")
        bucket = settings.default_bucket
    if not isinstance(bucket, str) or not _BUCKET_RE.match(bucket):
        raise ValidationError("nome de bucket inválido", operation="storage.validate")
    if not allowed:
        raise ConfigurationError("nenhum bucket permitido configurado", operation="storage.validate")
    if bucket not in allowed:
        raise ValidationError(f"bucket {bucket!r} fora da allowlist", operation="storage.validate", resource=bucket)
    return bucket


# --- tamanho ---------------------------------------------------------------------
def validate_size(size: Optional[int], max_bytes: int) -> None:
    """Recusa vazio, negativo e acima do teto (``FileTooLargeError``)."""
    if size is None:
        return
    if size <= 0:
        raise ValidationError("arquivo vazio não é permitido", operation="storage.validate")
    if size > max_bytes:
        raise FileTooLargeError(
            f"arquivo de {size} bytes excede o limite de {max_bytes} bytes", operation="storage.validate"
        )


# --- MIME ------------------------------------------------------------------------
_EXT_TO_MIME = {
    ".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".gif": "image/gif",
    ".webp": "image/webp", ".bmp": "image/bmp", ".ico": "image/x-icon", ".svg": "image/svg+xml",
    ".tif": "image/tiff", ".tiff": "image/tiff", ".heic": "image/heic", ".avif": "image/avif",
    ".mp3": "audio/mpeg", ".wav": "audio/x-wav", ".ogg": "audio/ogg", ".oga": "audio/ogg",
    ".m4a": "audio/mp4", ".aac": "audio/aac", ".flac": "audio/x-flac", ".opus": "audio/ogg",
    ".mp4": "video/mp4", ".m4v": "video/mp4", ".mov": "video/quicktime", ".webm": "video/webm",
    ".mkv": "video/x-matroska", ".avi": "video/x-msvideo", ".mpeg": "video/mpeg", ".mpg": "video/mpeg",
    ".pdf": "application/pdf", ".zip": "application/zip", ".gz": "application/gzip",
    ".7z": "application/x-7z-compressed", ".rar": "application/vnd.rar", ".tar": "application/x-tar",
    ".doc": "application/msword", ".xls": "application/vnd.ms-excel", ".ppt": "application/vnd.ms-powerpoint",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    ".pptx": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    ".txt": "text/plain", ".csv": "text/csv", ".md": "text/markdown", ".json": "application/json",
    ".xml": "application/xml", ".html": "text/html", ".htm": "text/html", ".js": "text/javascript",
    ".exe": "application/x-msdownload", ".dll": "application/x-msdownload",
}
_MIME_TO_EXT = {}
for _ext, _mime in _EXT_TO_MIME.items():  # primeira extensão registrada vence
    _MIME_TO_EXT.setdefault(_mime, _ext)

#: Tipos equivalentes (apelidos e contêineres compartilhados).
_COMPAT_GROUPS = (
    {"image/jpeg", "image/jpg", "image/pjpeg"},
    {"audio/mpeg", "audio/mp3", "audio/mpeg3", "audio/x-mpeg-3"},
    {"audio/x-wav", "audio/wav", "audio/wave", "audio/vnd.wave"},
    {"audio/x-flac", "audio/flac"},
    {"audio/x-aiff", "audio/aiff"},
    {"video/x-msvideo", "video/avi"},
    {"image/x-icon", "image/vnd.microsoft.icon"},
    {"application/gzip", "application/x-gzip"},
    {"application/x-rar-compressed", "application/vnd.rar"},
    {"video/mp4", "audio/mp4", "audio/x-m4a", "audio/m4a", "video/x-m4v"},
    {"video/webm", "audio/webm", "video/x-matroska", "audio/x-matroska"},
    {"video/ogg", "audio/ogg", "application/ogg"},
    {"application/msword", "application/vnd.ms-excel", "application/vnd.ms-powerpoint", "application/x-ole-storage"},
    {
        "application/zip", "application/x-zip", "application/x-zip-compressed", "application/epub+zip",
        "application/java-archive", "application/vnd.oasis.opendocument.text",
        "application/vnd.oasis.opendocument.spreadsheet", "application/vnd.oasis.opendocument.presentation",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    },
)
_GENERIC_CONTAINERS = frozenset({"application/zip", GENERIC_MIME})

#: Tipos/extensões que podem executar script no domínio de origem se servidos de bucket público.
DANGEROUS_PUBLIC_MIME = frozenset(
    {"text/html", "image/svg+xml", "text/javascript", "application/javascript", "application/x-msdownload",
     "application/x-executable", "application/x-sh", "application/x-dosexec", "application/x-msi"}
)
DANGEROUS_PUBLIC_EXT = frozenset(
    {".html", ".htm", ".svg", ".js", ".mjs", ".exe", ".dll", ".bat", ".cmd", ".sh", ".ps1", ".msi", ".com",
     ".scr", ".jar", ".php"}
)


def normalize_mime(value: Optional[str]) -> Optional[str]:
    """``"Text/Plain; charset=x"`` -> ``"text/plain"``; vazio -> ``None``."""
    if not value:
        return None
    base = value.split(";", 1)[0].strip().lower()
    return base or None


def mime_from_extension(filename: Optional[str]) -> Optional[str]:
    return _EXT_TO_MIME.get(extension_of(filename))


def extension_for_mime(mime: Optional[str]) -> str:
    return _MIME_TO_EXT.get(normalize_mime(mime) or "", "")


def mimes_compatible(a: str, b: str) -> bool:
    """Mesmo tipo ou apelidos/contêineres equivalentes."""
    return a == b or any(a in g and b in g for g in _COMPAT_GROUPS)


def mime_matches(mime: str, pattern: str) -> bool:
    """``image/*`` casa ``image/png``; ``*/*`` casa tudo."""
    pattern = pattern.strip().lower()
    if pattern in ("*", "*/*"):
        return True
    if pattern.endswith("/*"):
        return mime.startswith(pattern[:-1])
    return mime == pattern


def is_mime_allowed(mime: str, allowed: tuple[str, ...]) -> bool:
    return not allowed or any(mime_matches(mime, p) for p in allowed)


def detect_mime(head: bytes) -> Optional[str]:
    """Tipo pelo conteúdo (magic bytes dos primeiros bytes) ou ``None`` se não reconhecido."""
    if not head:
        return None
    kind = filetype.guess(head[:HEAD_BYTES])
    return kind.mime if kind is not None else None


def _is_detectable(mime: str) -> bool:
    """O ``filetype`` consegue reconhecer este tipo (ou um equivalente) pelo conteúdo?"""
    names = {mime}.union(*(g for g in _COMPAT_GROUPS if mime in g))
    return any(filetype.is_mime_supported(n) for n in names)


@dataclass(frozen=True)
class TypeEvidence:
    extension_mime: Optional[str]
    declared_mime: Optional[str]
    detected_mime: Optional[str]

    def describe(self) -> str:
        return (
            f"extensão={self.extension_mime or '?'}, declarado={self.declared_mime or '?'}, "
            f"detectado={self.detected_mime or '?'}"
        )


def check_type_consistency(evidence: TypeEvidence) -> None:
    """Extensão, MIME declarado e conteúdo precisam concordar; senão ``ValidationError``."""
    ext, declared, detected = evidence.extension_mime, evidence.declared_mime, evidence.detected_mime
    claims = [m for m in (ext, declared) if m]
    diverge = False
    if ext and declared and not mimes_compatible(ext, declared):
        diverge = True
    elif detected:
        diverge = any(not mimes_compatible(m, detected) for m in claims)
    else:  # conteúdo não reconhecido: ok para texto/desconhecido, mas não para binário que tem assinatura
        diverge = any(_is_detectable(m) for m in claims)
    if diverge:
        raise ValidationError(f"tipo de arquivo divergente ({evidence.describe()})", operation="storage.validate")


def choose_content_type(evidence: TypeEvidence) -> str:
    """Cadeia: detectado (se específico) > declarado > extensão > ``application/octet-stream``."""
    detected = evidence.detected_mime
    if detected and detected not in _GENERIC_CONTAINERS:
        return detected
    return evidence.declared_mime or evidence.extension_mime or detected or GENERIC_MIME


class FileValidator:
    """Validações de upload dirigidas por ``StorageSettings`` (bucket, tamanho, tipo)."""

    def __init__(self, settings: StorageSettings) -> None:
        self._settings = settings

    def resolve_bucket(self, bucket: Optional[str]) -> str:
        return resolve_bucket(bucket, self._settings)

    def validate_size(self, size: Optional[int]) -> None:
        validate_size(size, self._settings.max_file_bytes)

    def is_public(self, bucket: str) -> bool:
        return bucket in self._settings.buckets_public

    def resolve_content_type(
        self, *, filename: Optional[str], declared: Optional[str], head: bytes, public: bool = False
    ) -> str:
        """Confere extensão x declarado x conteúdo, a allowlist de MIME e (se público) tipos perigosos."""
        declared = normalize_mime(declared)
        if declared == GENERIC_MIME:
            declared = None  # genérico não informa nada
        evidence = TypeEvidence(mime_from_extension(filename), declared, detect_mime(head))
        check_type_consistency(evidence)
        content_type = choose_content_type(evidence)
        if not is_mime_allowed(content_type, self._settings.allowed_mime):
            raise ValidationError(f"tipo {content_type!r} não permitido", operation="storage.validate")
        if public and (content_type in DANGEROUS_PUBLIC_MIME or extension_of(filename) in DANGEROUS_PUBLIC_EXT):
            raise ValidationError(
                "tipo executável/ativo não é permitido em bucket público", operation="storage.validate"
            )
        return content_type
