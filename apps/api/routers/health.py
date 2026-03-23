"""Rotas de observabilidade para readiness/liveness."""

from __future__ import annotations

from collections.abc import Callable

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

router = APIRouter(tags=["health"])


def get_session_factory(request: Request) -> Callable[[], Session]:
    """Obtém a fabrica de sessão configurada no estado da aplicação."""

    return request.app.state.session_factory


@router.get("/health")
def health(request: Request) -> dict[str, str]:
    """Liveness probe simples para load balancer e container runtime."""

    app_version = getattr(request.app.state, "app_version", "0.0.0")
    return {"status": "ok", "version": app_version}


@router.get("/health/deep", include_in_schema=False)
def deep_health(
    session_factory: Callable[[], Session] = Depends(get_session_factory),
) -> dict[str, str]:
    """Readiness probe com verificação de conectividade ao banco."""

    try:
        with session_factory() as session:
            session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={"status": "degraded", "database": "disconnected"},
        ) from exc

    return {"status": "ok", "database": "connected"}
