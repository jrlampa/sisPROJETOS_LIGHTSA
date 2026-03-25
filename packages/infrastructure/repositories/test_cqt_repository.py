"""Testes unitários para o CQTRepository, com foco na lógica de persistência."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from packages.domain.cqt.models import (
    CentroCarga,
    Condutor,
    CQTAnalise,
    TipoRede,
    Transformador,
    TrechoEletrico,
)
from packages.domain.intake.models import TipoProjeto
from packages.infrastructure.database.models import (
    Base,
    CondutorORM,
    PosteProjetoORM,
    ProjetoORM,
    TrechoEletricoORM,
)
from packages.infrastructure.repositories.cqt_repository import CQTRepository

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
        codigo="P-TESTE",
        nome="Projeto Teste",
        localidade="Local Teste",
        etapa_atual="ENGENHARIA",
        checklist_triagem={},
        criado_em=datetime.now(timezone.utc),
    )
    session.add(projeto_orm)
    session.commit()
    return projeto_id


def test_salvar_analise_cqt_reutiliza_condutor_em_cache(db_session: Session):
    """
    Verifica se o CQTRepository reutiliza a mesma instância de CondutorORM
    quando múltiplos trechos usam o mesmo tipo de condutor, otimizando a persistência.
    """
    # Arrange
    projeto_id = _criar_projeto_no_banco(db_session)
    condutor_comum = Condutor(
        nome="Cabo Comum 70mm", resistencia_ohm_km=0.443, ampacidade_a=180
    )
    condutor_diferente = Condutor(
        nome="Cabo Diferente 35mm", resistencia_ohm_km=0.868, ampacidade_a=125
    )

    analise = CQTAnalise(
        tipo_projeto=TipoProjeto.RECONDUTORAMENTO,
        centro_carga=CentroCarga(
            nome="Centro Teste",
            transformador=Transformador("TR-123", 112.5, 80),
            trechos=[
                TrechoEletrico(
                    poste_de_codigo="P0",
                    poste_para_codigo="P1",
                    condutor=condutor_comum,
                    tipo_rede=TipoRede.CONVENCIONAL,
                    comprimento_m=100,
                    corrente_a=50,
                    ordem_no_circuito=1,
                ),
                TrechoEletrico(
                    poste_de_codigo="P1",
                    poste_para_codigo="P2",
                    condutor=condutor_diferente,
                    tipo_rede=TipoRede.CONVENCIONAL,
                    comprimento_m=50,
                    corrente_a=30,
                    ordem_no_circuito=2,
                ),
                TrechoEletrico(
                    poste_de_codigo="P2",
                    poste_para_codigo="P3",
                    condutor=condutor_comum,
                    tipo_rede=TipoRede.CONVENCIONAL,
                    comprimento_m=120,
                    corrente_a=60,
                    ordem_no_circuito=3,
                ),
            ],
        ),
    )

    # Act
    repo = CQTRepository(db_session)
    repo.salvar_analise_cqt(projeto_id, analise)
    db_session.commit()

    # Assert
    # Deve haver apenas 2 condutores, pois um é repetido
    total_condutores_db = db_session.scalar(select(func.count(CondutorORM.id)))
    assert total_condutores_db == 2

    # Verifica se os trechos 1 e 3 apontam para o mesmo condutor_id
    trechos_db = db_session.scalars(
        select(TrechoEletricoORM).order_by(TrechoEletricoORM.ordem_no_circuito)
    ).all()
    assert len(trechos_db) == 3

    trecho1_db = trechos_db[0]
    trecho2_db = trechos_db[1]
    trecho3_db = trechos_db[2]
 
    assert trecho1_db.condutor_id == trecho3_db.condutor_id
    assert trecho1_db.condutor_id != trecho2_db.condutor_id
    assert trecho1_db.condutor.nome == "Cabo Comum 70mm"
    assert trecho2_db.condutor.nome == "Cabo Diferente 35mm"


def test_salvar_analise_cqt_com_condutores_diferentes(db_session: Session):
    """
    Verifica se o CQTRepository cria um CondutorORM para cada condutor
    distinto quando não há repetição.
    """
    # Arrange
    projeto_id = _criar_projeto_no_banco(db_session)
    analise = CQTAnalise(
        tipo_projeto=TipoProjeto.RECONDUTORAMENTO,
        centro_carga=CentroCarga(
            nome="Centro Teste",
            transformador=Transformador("TR-123", 112.5, 80),
            trechos=[
                TrechoEletrico(
                    poste_de_codigo="PA",
                    poste_para_codigo="PB",
                    condutor=Condutor("Cabo A", 1.0, 100),
                    tipo_rede=TipoRede.CONVENCIONAL,
                    comprimento_m=100,
                    corrente_a=50,
                    ordem_no_circuito=1,
                ),
                TrechoEletrico(
                    poste_de_codigo="PB",
                    poste_para_codigo="PC",
                    condutor=Condutor("Cabo B", 2.0, 200),
                    tipo_rede=TipoRede.CONVENCIONAL,
                    comprimento_m=50,
                    corrente_a=30,
                    ordem_no_circuito=2,
                ),
            ],
        ),
    )

    # Act
    repo = CQTRepository(db_session)
    repo.salvar_analise_cqt(projeto_id, analise)
    db_session.commit()

    # Assert
    total_condutores_db = db_session.scalar(select(func.count(CondutorORM.id)))
    assert total_condutores_db == 2


def test_salvar_analise_cqt_cria_postes_stub(db_session: Session):
    """
    Verifica se o CQTRepository, ao salvar uma análise, cria os postes
    referenciados pelos trechos na tabela unificada `postes_projeto`.
    """
    # Arrange
    projeto_id = _criar_projeto_no_banco(db_session)
    analise = CQTAnalise(
        tipo_projeto=TipoProjeto.RECONDUTORAMENTO,
        centro_carga=CentroCarga(
            nome="Centro Teste",
            transformador=Transformador("TR-123", 112.5, 80),
            trechos=[
                TrechoEletrico(
                    poste_de_codigo="P-CQT-01",
                    poste_para_codigo="P-CQT-02",
                    condutor=Condutor("Cabo A", 1.0, 100),
                    tipo_rede=TipoRede.CONVENCIONAL,
                    comprimento_m=100,
                    corrente_a=50,
                    ordem_no_circuito=1,
                )
            ],
        ),
    )
    repo = CQTRepository(db_session)
    repo.salvar_analise_cqt(projeto_id, analise)
    db_session.commit()
    total_postes_db = db_session.scalar(select(func.count(PosteProjetoORM.id)))
    assert total_postes_db == 2