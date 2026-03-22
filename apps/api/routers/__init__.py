"""Routers HTTP da API."""

from .cad import router as cad_router
from .cqt import router as cqt_router
from .projetos import router as projetos_router

__all__ = ["cad_router", "cqt_router", "projetos_router"]
