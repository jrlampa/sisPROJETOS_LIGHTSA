"""Configuracao de sessoes SQLAlchemy para persistencia local-first."""

from __future__ import annotations

import sqlite3
from collections.abc import Callable

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool


def build_engine(database_url: str) -> Engine:
    """Cria engine SQLAlchemy apropriada para SQLite local-first.

    Usa StaticPool para bancos SQLite em memoria, permitindo que a base persista
    entre multiplas sessoes durante testes de integracao.
    """

    engine_kwargs: dict = {"future": True}
    if database_url.startswith("sqlite"):
        engine_kwargs["connect_args"] = {"check_same_thread": False}
        if ":memory:" in database_url:
            engine_kwargs["poolclass"] = StaticPool

    engine = create_engine(database_url, **engine_kwargs)

    if database_url.startswith("sqlite"):

        @event.listens_for(engine, "connect")
        def _set_sqlite_pragmas(dbapi_connection, connection_record) -> None:  # type: ignore[no-untyped-def]
            del connection_record
            if isinstance(dbapi_connection, sqlite3.Connection):
                cursor = dbapi_connection.cursor()
                cursor.execute("PRAGMA journal_mode=WAL;")
                cursor.execute("PRAGMA synchronous=NORMAL;")
                cursor.close()

    return engine


def create_session_factory(
    database_url: str,
    *,
    engine: Engine | None = None,
) -> Callable[[], Session]:
    """Retorna uma fabrica de sessoes para casos de uso e repositórios."""

    engine = engine or build_engine(database_url)
    factory = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
    return factory
