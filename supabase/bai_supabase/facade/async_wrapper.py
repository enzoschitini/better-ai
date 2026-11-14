"""Wrapper assíncrono por thread (decisão D-02): o contrato é síncrono; aqui só se
move a execução para threads, sem bloquear o event loop (FastAPI)."""

from __future__ import annotations

import asyncio
from typing import Any, Callable, Optional, TypeVar

from bai_supabase.contracts.results import CompositeResult
from bai_supabase.contracts.storage import FileSource, UploadOptions
from bai_supabase.facade.integration import FileRef, SupabaseIntegration

T = TypeVar("T")


class AsyncSupabaseIntegration:
    def __init__(self, integration: SupabaseIntegration, max_concurrency: int = 4) -> None:
        if max_concurrency < 1:
            raise ValueError("max_concurrency deve ser >= 1")
        self._integration = integration
        self._sem = asyncio.Semaphore(max_concurrency)

    @property
    def sync(self) -> SupabaseIntegration:
        return self._integration

    async def run(self, fn: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Executa qualquer chamada síncrona da integração em thread, com limite de concorrência."""
        async with self._sem:
            return await asyncio.to_thread(fn, *args, **kwargs)

    async def save_file_with_record(self, *args: Any, **kwargs: Any) -> CompositeResult:
        return await self.run(self._integration.save_file_with_record, *args, **kwargs)

    async def replace_file_in_record(self, *args: Any, **kwargs: Any) -> CompositeResult:
        return await self.run(self._integration.replace_file_in_record, *args, **kwargs)

    async def delete_record_and_file(self, *args: Any, **kwargs: Any) -> CompositeResult:
        return await self.run(self._integration.delete_record_and_file, *args, **kwargs)

    async def upload(self, source: FileSource, options: Optional[UploadOptions] = None):
        return await self.run(self._integration.storage.upload, source, options)

    async def download(self, path: str, bucket: Optional[str] = None) -> bytes:
        return await self.run(self._integration.storage.download, path, bucket)
