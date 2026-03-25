"""Testes unitários para o PosteRepository."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from packages.domain.tracao.models import Poste
from packages.infrastructure.database.models import Base, PosteProjetoORM, ProjetoORM
from packages.infrastructure.repositories.poste_repository import PosteRepository

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
        codigo="P-TESTE-POSTE",
        nome="Projeto Teste Poste",
        localidade="Local Teste",
        etapa_atual="ENGENHARIA",
        checklist_triagem={},
        criado_em=datetime.now(timezone.utc),
    )
    session.add(projeto_orm)
    session.commit()
    return projeto_id


def test_get_or_create_cria_novo_poste_e_enriquece_dados(db_session: Session):
    """Verifica se get_or_create cria um novo PosteProjetoORM e preenche os dados de tração."""
    # Arrange
    projeto_id = _criar_projeto_no_banco(db_session)
    poste_domain = Poste(codigo="P-01", resistencia_nominal_daN=300)
    cache: dict[str, PosteProjetoORM] = {}
    repo = PosteRepository(db_session)

    # Act
    poste_orm = repo.get_or_create(projeto_id, poste_domain, cache)
    db_session.commit()

    # Assert
    assert isinstance(poste_orm, PosteProjetoORM)
    assert poste_orm.codigo == "P-01"
    assert poste_orm.resistencia_nominal_daN == 300
    assert "P-01" in cache
    assert cache["P-01"] is poste_orm

    total_postes_db = db_session.scalar(select(func.count(PosteProjetoORM.id)))
    assert total_postes_db == 1


def test_get_or_create_reutiliza_do_cache_e_enriquece(db_session: Session):
    """Verifica se get_or_create reutiliza um poste do cache e atualiza seus dados."""
    # Arrange
    projeto_id = _criar_projeto_no_banco(db_session)
    # Poste já existe no cache, mas sem dados de tração (criado como stub pelo CQT)
    poste_orm_existente = PosteProjetoORM(id=str(uuid4()), projeto_id=str(projeto_id), codigo="P-01")
    cache = {"P-01": poste_orm_existente}

    # Novos dados de domínio (da análise de tração)
    poste_domain_com_dados = Poste(codigo="P-01", resistencia_nominal_daN=600)
    repo = PosteRepository(db_session)

    # Act
    poste_orm_obtido = repo.get_or_create(projeto_id, poste_domain_com_dados, cache)

    # Assert
    assert poste_orm_obtido is poste_orm_existente  # Deve ser a mesma instância
    assert poste_orm_obtido.resistencia_nominal_daN == 600  # Dados foram enriquecidos


def test_get_or_create_stub_cria_novo_poste(db_session: Session):
    """Verifica se get_or_create_stub cria um novo poste apenas com código."""
    # Arrange
    projeto_id = _criar_projeto_no_banco(db_session)
    cache: dict[str, PosteProjetoORM] = {}
    repo = PosteRepository(db_session)

    # Act
    poste_orm = repo.get_or_create_stub(projeto_id, "P-STUB-01", cache)
    db_session.commit()

    # Assert
    assert poste_orm.codigo == "P-STUB-01"
    assert poste_orm.resistencia_nominal_daN is None  # Não deve ter dados de tração
    assert "P-STUB-01" in cache

    total_postes_db = db_session.scalar(select(func.count(PosteProjetoORM.id)))
    assert total_postes_db == 1


def test_get_or_create_stub_reutiliza_do_cache(db_session: Session):
    """Verifica se get_or_create_stub retorna a instância do cache se o poste já existir."""
    # Arrange
    projeto_id = _criar_projeto_no_banco(db_session)
    poste_orm_existente = PosteProjetoORM(id=str(uuid4()), projeto_id=str(projeto_id), codigo="P-STUB-01")
    cache = {"P-STUB-01": poste_orm_existente}
    repo = PosteRepository(db_session)

    # Act
    poste_orm_obtido = repo.get_or_create_stub(projeto_id, "P-STUB-01", cache)

    # Assert
    assert poste_orm_obtido is poste_orm_existente