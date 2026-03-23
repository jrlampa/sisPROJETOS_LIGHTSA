"""Routers HTTP da API."""

from .auth import router as auth_router
from .cad import router as cad_router
from .cqt import router as cqt_router
from .exportacao import router as exportacao_router
from .health import router as health_router
from .projetos import router as projetos_router
from .tracao import router as tracao_router

__all__ = [
	"auth_router",
	"cad_router",
	"cqt_router",
	"exportacao_router",
	"health_router",
	"projetos_router",
	"tracao_router",
]
