"""Entry point da API HTTP do sisPROJETOS LIGHT S.A."""

from __future__ import annotations

import os

from fastapi import FastAPI

from apps.api.routers.cad import router as cad_router
from apps.api.routers.cqt import router as cqt_router
from apps.api.routers.projetos import router as projetos_router
from packages.infrastructure.database.models import Base
from packages.infrastructure.database.session import build_engine, create_session_factory


def create_app(database_url: str | None = None) -> FastAPI:
    """Cria a aplicacao FastAPI com infraestrutura local-first inicializada."""

    resolved_database_url = database_url or os.getenv(
        "DATABASE_URL", "sqlite+pysqlite:///./sisprojetos_local.db"
    )

    app = FastAPI(title="sisPROJETOS LIGHT S.A.", version="0.1.0")

    engine = build_engine(resolved_database_url)
    Base.metadata.create_all(bind=engine)
    app.state.session_factory = create_session_factory(resolved_database_url, engine=engine)

    app.include_router(projetos_router)
    app.include_router(cqt_router)
    app.include_router(cad_router)

    @app.get("/")
    def hello_world() -> dict[str, str]:
        return {"message": "Hello World - sisPROJETOS LIGHT API"}

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "api"}

    return app


app = create_app()
