"""Dependencias FastAPI compartilhadas entre routers."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import Request
from sqlalchemy.orm import Session


def get_session_factory(request: Request) -> Callable[[], Session]:
    """Obtem a fabrica de sessao configurada no estado da aplicacao."""

    return request.app.state.session_factory
