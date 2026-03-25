"""Testes unitários para a BaseRepository."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from packages.infrastructure.database.models import Base, ProjetoORM
from packages.infrastructure.repositories.base_repository import BaseRepository

# Setup para banco de dados SQLite em memória para os testes
engine = create_engine("sqlite:///:memory:")
TestingSessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Session:
    """Cria e limpa o schema do banco de dados para cada teste, retornando uma sessão."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionFactory()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


def _criar_projeto_no_banco(session: Session) -> UUID:
    """Helper para criar um projeto dummy no banco e retornar seu ID."""
    projeto_id = uuid4()
    projeto_orm = ProjetoORM(
        id=str(projeto_id),
        codigo="P-TESTE-BASE",
        nome="Projeto Teste Base",
        localidade="Local Teste",
        etapa_atual="ENGENHARIA",
        checklist_triagem={},
        criado_em=datetime.now(timezone.utc),
    )
    session.add(projeto_orm)
    session.commit()
    return projeto_id


def test_get_projeto_orm_sucesso(db_session: Session):
    """Verifica se _get_projeto_orm retorna o projeto correto quando ele existe."""
    # Arrange
    projeto_id = _criar_projeto_no_banco(db_session)
    repo = BaseRepository(db_session)

    # Act
    projeto_orm = repo._get_projeto_orm(projeto_id, "Erro inesperado")

    # Assert
    assert isinstance(projeto_orm, ProjetoORM)
    assert projeto_orm.id == str(projeto_id)
    assert projeto_orm.codigo == "P-TESTE-BASE"


def test_get_projeto_orm_falha_com_excecao(db_session: Session):
    """Verifica se _get_projeto_orm lança ValueError quando o projeto não existe."""
    # Arrange
    projeto_id_inexistente = uuid4()
    repo = BaseRepository(db_session)
    mensagem_erro = "Projeto não foi encontrado!"

    # Act & Assert
    with pytest.raises(ValueError, match=mensagem_erro):
        repo._get_projeto_orm(projeto_id_inexistente, mensagem_erro)