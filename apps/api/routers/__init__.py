"""Routers HTTP da API."""

from .cqt import router as cqt_router
from .projetos import router as projetos_router

__all__ = ["cqt_router", "projetos_router"]
