"""Fixtures globais. Testes offline NUNCA tocam a rede (constituição P9)."""
from __future__ import annotations

import socket

import pytest


class NetworkBlockedError(RuntimeError):
    pass


@pytest.fixture(autouse=True)
def _block_network(request, monkeypatch):
    """Bloqueia sockets em testes que não sejam integration/e2e."""
    if request.node.get_closest_marker("integration") or request.node.get_closest_marker("e2e"):
        return

    real_connect = socket.socket.connect
    real_create = socket.create_connection

    def _is_loopback(address) -> bool:
        host = address[0] if isinstance(address, tuple) and address else address
        return host in ("127.0.0.1", "::1", "localhost")

    def _connect(self, address):
        if _is_loopback(address):  # asyncio usa socketpair local: não é rede externa
            return real_connect(self, address)
        raise NetworkBlockedError("rede bloqueada em teste offline")

    def _create(address, *args, **kwargs):
        if _is_loopback(address):
            return real_create(address, *args, **kwargs)
        raise NetworkBlockedError("rede bloqueada em teste offline")

    monkeypatch.setattr(socket.socket, "connect", _connect)
    monkeypatch.setattr(socket, "create_connection", _create)
