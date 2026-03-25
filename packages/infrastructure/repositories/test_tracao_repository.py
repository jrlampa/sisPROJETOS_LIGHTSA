"""Testes unitários para o TracaoRepository e o novo PosteRepository."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session, sessionmaker

from packages.domain.tracao.models import EstadoMecanico, Poste, ResultadoTracao
from packages.infrastructure.database.models import (
    Base,
    PosteProjetoORM,
    ProjetoORM,
    ResultadoTracaoORM,
)
from packages.infrastructure.repositories.tracao_repository import TracaoRepository

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
        codigo="P-TESTE-TRACAO",
        nome="Projeto Teste Tracao",
        localidade="Local Teste",
        etapa_atual="ENGENHARIA",
        checklist_triagem={},
        criado_em=datetime.now(timezone.utc),
    )
    session.add(projeto_orm)
    session.commit()
    return projeto_id


def test_salvar_resultados_tracao_reutiliza_poste_para_entradas_duplicadas(
    db_session: Session,
):
    """
    Verifica se o TracaoRepository, ao salvar resultados, cria apenas um registro
    de PosteProjetoORM para postes com o mesmo código, reutilizando-o e associando
    o último resultado processado.
    """
    # Arrange
    projeto_id = _criar_projeto_no_banco(db_session)
    poste_1 = Poste(codigo="P-01", resistencia_nominal_daN=300)
    resultado_1_inicial = ResultadoTracao.calcular(poste_1)

    poste_2 = Poste(codigo="P-02", resistencia_nominal_daN=600)
    resultado_2 = ResultadoTracao.calcular(poste_2)

    # Reutilizando poste_1 com um novo resultado (simula uma re-análise)
    resultado_1_final = ResultadoTracao(
        poste=poste_1,
        esforco_resultante_daN=200,
        percentual_carregamento=66.6,
        estado_mecanico=EstadoMecanico.APROVADO,
        calculado_em=datetime.now(timezone.utc),
    )

    lista_de_resultados = [
        (poste_1, resultado_1_inicial),
        (poste_2, resultado_2),
        (poste_1, resultado_1_final),  # Poste 1 aparece de novo com resultado atualizado
    ]
    repo = TracaoRepository(db_session)

    # Act
    repo.salvar_resultados_tracao(projeto_id, lista_de_resultados)
    db_session.commit()

    # Assert
    # 1. Deve haver apenas 2 postes no banco (P-01 e P-02)
    total_postes_db = db_session.scalar(select(func.count(PosteProjetoORM.id)))
    assert total_postes_db == 2

    # 2. Deve haver 2 resultados no banco (o último resultado para cada poste prevalece)
    total_resultados_db = db_session.scalar(select(func.count(ResultadoTracaoORM.id)))
    assert total_resultados_db == 2

    # 3. Verifica se o resultado final do P-01 é o último que foi processado
    poste_1_db = db_session.scalars(
        select(PosteProjetoORM).where(PosteProjetoORM.codigo == "P-01")
    ).one()
    assert poste_1_db.resultado is not None
    assert poste_1_db.resultado.esforco_resultante_daN == pytest.approx(200)
    assert poste_1_db.resultado.id == str(resultado_1_final.id)