"""Entry point da API HTTP do sisPROJETOS LIGHT S.A."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, ORJSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import ValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from apps.api.core.logger import setup_file_logging
from apps.api.routers.auth import router as auth_router
from apps.api.routers.cad import router as cad_router
from apps.api.routers.cqt import router as cqt_router
from apps.api.routers.exportacao import router as exportacao_router
from apps.api.routers.health import router as health_router
from apps.api.routers.projetos import router as projetos_router
from apps.api.routers.tracao import router as tracao_router
from packages.infrastructure.database.session import build_engine, create_session_factory

log_path = setup_file_logging()
logger = logging.getLogger(__name__)
VERSION_FILE = Path(__file__).resolve().parents[2] / "VERSION"


def read_app_version() -> str:
    """Le versao da aplicacao a partir do arquivo VERSION na raiz."""

    try:
        version = VERSION_FILE.read_text(encoding="utf-8").strip()
    except OSError:
        return "0.0.0"
    return version or "0.0.0"


def _normalizar_erro_validacao(exc: RequestValidationError) -> str:
    """Traduz erros comuns de validacao para mensagens objetivas em portugues."""

    for erro in exc.errors():
        if erro.get("type") == "json_invalid":
            return "JSON invalido no corpo da requisicao."
    return "Dados invalidos enviados para a API."


class SPAStaticFiles(StaticFiles):
    """Servidor de assets com fallback para index.html (SPA React Router)."""

    async def get_response(self, path: str, scope):  # type: ignore[override]
        try:
            return await super().get_response(path, scope)
        except StarletteHTTPException as exc:
            if exc.status_code == status.HTTP_404_NOT_FOUND:
                return await super().get_response("index.html", scope)
            raise


def create_app(database_url: str | None = None) -> FastAPI:
    """Cria a aplicacao FastAPI com infraestrutura local-first inicializada."""

    resolved_database_url = database_url or os.getenv(
        "DATABASE_URL", "sqlite+pysqlite:///./sisprojetos_local.db"
    )
    app_version = read_app_version()
    logger.info("Inicializando API FastAPI com logging em ficheiro: %s", log_path)

    app = FastAPI(
        title="sisPROJETOS LIGHT S.A.",
        version=app_version,
        default_response_class=ORJSONResponse,
    )
    app.state.app_version = app_version

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost",
            "http://localhost:3000",
            "http://127.0.0.1",
            "http://127.0.0.1:3000",
        ],
        allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    engine = build_engine(resolved_database_url)
    # Para SQLite em memoria (testes) cria o esquema diretamente;
    # em producao o esquema e gerido por migracoes Alembic.
    if ":memory:" in resolved_database_url:
        from packages.infrastructure.database.models import Base

        Base.metadata.create_all(bind=engine)
    app.state.session_factory = create_session_factory(resolved_database_url, engine=engine)

    app.include_router(auth_router, prefix="/api")
    app.include_router(projetos_router, prefix="/api")
    app.include_router(cqt_router, prefix="/api")
    app.include_router(cad_router, prefix="/api")
    app.include_router(tracao_router, prefix="/api")
    app.include_router(exportacao_router, prefix="/api")
    app.include_router(health_router, prefix="/api")

    @app.exception_handler(RequestValidationError)
    async def request_validation_exception_handler(
        request: Request,
        exc: RequestValidationError,
    ) -> JSONResponse:
        logger.error(
            "RequestValidationError em %s %s: %s",
            request.method,
            request.url.path,
            exc,
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": _normalizar_erro_validacao(exc),
                "errors": exc.errors(),
            },
        )

    @app.exception_handler(ValidationError)
    async def pydantic_validation_exception_handler(
        request: Request,
        exc: ValidationError,
    ) -> JSONResponse:
        logger.error(
            "ValidationError em %s %s: %s",
            request.method,
            request.url.path,
            exc,
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": "Dados invalidos para processamento.",
                "errors": exc.errors(),
            },
        )

    @app.exception_handler(ValueError)
    async def value_error_exception_handler(request: Request, exc: ValueError) -> JSONResponse:
        logger.error(
            "ValueError em %s %s: %s",
            request.method,
            request.url.path,
            exc,
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"detail": str(exc) or "Requisicao invalida."},
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.error(
            "Erro nao tratado em %s %s: %s",
            request.method,
            request.url.path,
            exc,
            exc_info=True,
        )
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={"detail": "Nao foi possivel processar a requisicao."},
        )

    web_dist_dir = Path(__file__).resolve().parents[2] / "apps" / "web" / "dist"
    if web_dist_dir.exists():
        app.mount(
            "/",
            SPAStaticFiles(directory=str(web_dist_dir), html=True),
            name="web",
        )

    return app


app = create_app()
