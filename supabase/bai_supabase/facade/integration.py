"""Classe integradora (fachada) — research/08, constituição P2.

Compõe a classe de tabelas e a de arquivos. NÃO contém lógica de tabela nem de storage:
só delega e orquestra operações combinadas (arquivo + registro), com ordem fixa e
compensação de melhor esforço. As duas frentes não se conhecem.
"""

from __future__ import annotations

import uuid
from typing import Any, Callable, Optional, Union

from bai_supabase.contracts.logging import LoggerContract
from bai_supabase.contracts.results import CompositeResult, CompositeStatus, StoredFile
from bai_supabase.contracts.storage import CollisionPolicy, FileSource, FileStore, UploadOptions
from bai_supabase.contracts.tables import TablesContract
from bai_supabase.errors.exceptions import SupabaseIntegrationError

FileRef = tuple[str, str]  # (bucket, path)


class SupabaseIntegration:
    """Ponto único de entrada do backend para o Supabase."""

    def __init__(self, tables: TablesContract, storage: FileStore, logger: LoggerContract) -> None:
        self._tables = tables
        self._storage = storage
        self._log = logger

    # --- delegação pura (sem lógica própria) -------------------------------------
    @property
    def tables(self) -> TablesContract:
        return self._tables

    @property
    def storage(self) -> FileStore:
        return self._storage

    # --- operações combinadas ----------------------------------------------------
    def save_file_with_record(
        self,
        table: str,
        source: FileSource,
        record_factory: Callable[[StoredFile], Any],
        options: Optional[UploadOptions] = None,
    ) -> CompositeResult:
        """Grava: arquivo -> registro. Se o registro falhar, tenta apagar o arquivo (melhor esforço)."""
        cid = _new_cid()
        log = self._log.bind(correlation_id=cid, operation="composite.save_file_with_record", table=table)
        steps: list[str] = []
        opts = _with_cid(options, cid)
        try:
            stored = self._storage.upload(source, opts)
        except SupabaseIntegrationError as exc:
            return CompositeResult(CompositeStatus.FALHOU, steps, False, cid, error=exc)
        steps.append("arquivo_gravado")

        try:
            record = self._tables.table(table).insert(record_factory(stored))
        except SupabaseIntegrationError as exc:
            orphan = not self._compensate_delete(log, stored.bucket, stored.path)
            return self._failure(steps, exc, cid, orphan, stored_file=stored if orphan else None)
        steps.append("registro_gravado")
        log.info("composite.completa", steps=steps)
        return CompositeResult(CompositeStatus.COMPLETA, steps, False, cid, record=record, stored_file=stored)

    def replace_file_in_record(
        self,
        table: str,
        record_id: Any,
        source: FileSource,
        changes_factory: Callable[[StoredFile], dict],
        old_ref: Optional[FileRef] = None,
        options: Optional[UploadOptions] = None,
    ) -> CompositeResult:
        """Substitui: novo arquivo (caminho novo) -> atualiza registro -> apaga o antigo por último."""
        cid = _new_cid()
        log = self._log.bind(correlation_id=cid, operation="composite.replace_file_in_record", table=table)
        steps: list[str] = []
        opts = _with_cid(_force_new_path(options), cid)
        try:
            stored = self._storage.upload(source, opts)
        except SupabaseIntegrationError as exc:
            return CompositeResult(CompositeStatus.FALHOU, steps, False, cid, error=exc)
        steps.append("arquivo_novo_gravado")

        try:
            record = self._tables.table(table).update(record_id, changes_factory(stored))
        except SupabaseIntegrationError as exc:
            orphan = not self._compensate_delete(log, stored.bucket, stored.path)
            return self._failure(steps, exc, cid, orphan, stored_file=stored if orphan else None)
        steps.append("registro_atualizado")

        if old_ref is not None:
            exc = self._remove_file(old_ref[0], old_ref[1])
            if exc is not None:
                self._log_orphan(log, old_ref[0], old_ref[1], exc)
                return CompositeResult(
                    CompositeStatus.PARCIAL, steps, True, cid, record=record, stored_file=stored, error=exc
                )
            steps.append("arquivo_antigo_apagado")
        log.info("composite.completa", steps=steps)
        return CompositeResult(CompositeStatus.COMPLETA, steps, False, cid, record=record, stored_file=stored)

    def delete_record_and_file(self, table: str, record_id: Any, file_ref: Optional[FileRef]) -> CompositeResult:
        """Apaga: registro primeiro, arquivo depois (nunca deixa registro apontando para o nada)."""
        cid = _new_cid()
        log = self._log.bind(correlation_id=cid, operation="composite.delete_record_and_file", table=table)
        steps: list[str] = []
        try:
            self._tables.table(table).delete(record_id)
        except SupabaseIntegrationError as exc:
            return CompositeResult(CompositeStatus.FALHOU, steps, False, cid, error=exc)
        steps.append("registro_apagado")

        if file_ref is not None:
            exc = self._remove_file(file_ref[0], file_ref[1])
            if exc is not None:
                self._log_orphan(log, file_ref[0], file_ref[1], exc)
                return CompositeResult(CompositeStatus.PARCIAL, steps, True, cid, error=exc)
            steps.append("arquivo_apagado")
        log.info("composite.completa", steps=steps)
        return CompositeResult(CompositeStatus.COMPLETA, steps, False, cid)

    # --- internos ---------------------------------------------------------------
    def _compensate_delete(self, log: LoggerContract, bucket: str, path: str) -> bool:
        """Melhor esforço: True se apagou. Se falhar NÃO propaga segundo erro; só registra órfão."""
        exc = self._remove_file(bucket, path)
        if exc is None:
            log.info("composite.compensacao_ok", bucket=bucket, path=path)
            return True
        self._log_orphan(log, bucket, path, exc)
        return False

    def _remove_file(self, bucket: str, path: str) -> Optional[SupabaseIntegrationError]:
        """Apaga um arquivo. ``None`` = ok. ``storage.delete`` pode devolver falhas no relatório
        (sem levantar), então o relatório também é conferido."""
        try:
            report = self._storage.delete([path], bucket=bucket)
        except SupabaseIntegrationError as exc:
            return exc
        reason = report.failed.get(path)
        if reason is None:
            return None
        return SupabaseIntegrationError(
            f"falha ao apagar arquivo: {reason}", operation="storage.delete", resource=f"{bucket}/{path}"
        )

    @staticmethod
    def _log_orphan(log: LoggerContract, bucket: str, path: str, exc: SupabaseIntegrationError) -> None:
        log.error(
            "composite.orfao_possivel",
            orfao_possivel=True,
            bucket=bucket,
            path=path,
            exception_class=type(exc).__name__,
            provider_code=exc.provider_code,
        )

    @staticmethod
    def _failure(
        steps: list[str],
        exc: SupabaseIntegrationError,
        cid: str,
        orphan: bool,
        stored_file: Optional[StoredFile] = None,
    ) -> CompositeResult:
        # Compensou => nada sobrou (falhou). Não compensou => sobrou arquivo (parcial).
        status = CompositeStatus.PARCIAL if orphan else CompositeStatus.FALHOU
        return CompositeResult(status, steps, orphan, cid, stored_file=stored_file, error=exc)


def _new_cid() -> str:
    return uuid.uuid4().hex[:12]


def _with_cid(options: Optional[UploadOptions], cid: str) -> UploadOptions:
    from dataclasses import replace

    base = options or UploadOptions()
    return replace(base, correlation_id=base.correlation_id or cid)


def _force_new_path(options: Optional[UploadOptions]) -> UploadOptions:
    """Substituir arquivo nunca reaproveita o caminho (decisão A-08): descarta ``path`` e usa REJECT."""
    from dataclasses import replace

    base = options or UploadOptions()
    return replace(base, path=None, collision=CollisionPolicy.REJECT)
