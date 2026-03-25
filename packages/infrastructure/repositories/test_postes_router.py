"""Testes de integração para o router de Postes."""

from __future__ import annotations

from datetime import datetime, timezone
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from apps.api.main import app
from packages.domain.cqt.models import TipoRede
from packages.domain.intake.models import TipoProjeto
from packages.domain.tracao.models import EstadoMecanico
from packages.infrastructure.database.models import (
    CentroCargaORM,
    CondutorORM,
    CQTAnaliseORM,
    PosteProjetoORM,
    ProjetoORM,
    ResultadoTracaoORM,
    TransformadorORM,
    TrechoEletricoORM,
)

client = TestClient(app)


def _seed_database(session: Session) -> tuple[str, str]:
    """Popula o banco com um projeto, postes, uma análise CQT e um resultado de tração."""
    # 1. Projeto
    projeto_id = str(uuid4())
    session.add(
        ProjetoORM(
            id=projeto_id,
            codigo="PROJ-CONSOLIDADO",
            nome="Projeto de Teste para Consolidação",
            localidade="Teste",
            etapa_atual="ENGENHARIA",
            criado_em=datetime.now(timezone.utc),
        )
    )

    # 2. Postes
    p1 = PosteProjetoORM(id=str(uuid4()), projeto_id=projeto_id, codigo="P1", resistencia_nominal_daN=300)
    p2 = PosteProjetoORM(id=str(uuid4()), projeto_id=projeto_id, codigo="P2")
    p3 = PosteProjetoORM(id=str(uuid4()), projeto_id=projeto_id, codigo="P3")
    session.add_all([p1, p2, p3])

    # 3. Análise CQT (conectando P1 e P2)
    analise_id = str(uuid4())
    centro_id = str(uuid4())
    trafo_id = str(uuid4())
    condutor_id = str(uuid4())
    trecho_id = str(uuid4())

    session.add(
        CQTAnaliseORM(
            id=analise_id,
            projeto_id=projeto_id,
            tipo_projeto=TipoProjeto.RECONDUTORAMENTO.value,
            centro_carga=CentroCargaORM(
                id=centro_id,
                nome="Centro Teste",
                transformador=TransformadorORM(id=trafo_id, descricao="TR-TESTE", potencia_nominal_kva=112.5),
                trechos=[
                    TrechoEletricoORM(
                        id=trecho_id,
                        poste_de_id=p1.id,
                        poste_para_id=p2.id,
                        tipo_rede=TipoRede.CONVENCIONAL.value,
                        comprimento_m=50,
                        condutor=CondutorORM(id=condutor_id, nome="Cabo 70mm", resistencia_ohm_km=0.4, ampacidade_a=180),
                    )
                ],
            ),
        )
    )

    # 4. Resultado de Tração (para P1)
    resultado_id = str(uuid4())
    session.add(
        ResultadoTracaoORM(
            id=resultado_id,
            poste_id=p1.id,
            esforco_resultante_daN=150.0,
            percentual_carregamento=50.0,
            estado_mecanico=EstadoMecanico.APROVADO.value,
            calculado_em=datetime.now(timezone.utc),
        )
    )

    session.commit()
    return projeto_id, p1.id


def test_obter_poste_consolidado_sucesso(db_session: Session):
    """
    Valida o endpoint para um poste que possui dados de tração e CQT.
    A resposta deve conter a consolidação de todas as informações.
    """
    # Arrange
    projeto_id, poste_1_id = _seed_database(db_session)

    # Act
    response = client.get(f"/api/projetos/{projeto_id}/postes/P1")

    # Assert
    assert response.status_code == 200
    data = response.json()

    assert data["id"] == poste_1_id
    assert data["codigo"] == "P1"
    assert data["resistencia_nominal_daN"] == 300

    # Valida dados de tração
    assert data["resultado_tracao"] is not None
    assert data["resultado_tracao"]["esforco_resultante_daN"] == 150.0
    assert data["resultado_tracao"]["estado_mecanico"] == "APROVADO"

    # Valida dados de CQT (trechos conectados)
    assert len(data["trechos_conectados"]) == 1
    trecho = data["trechos_conectados"][0]
    assert trecho["nome"] == "P1-P2"
    assert trecho["tipo_conexao"] == "de"
    assert trecho["condutor_nome"] == "Cabo 70mm"


def test_obter_poste_consolidado_sem_dados_associados(db_session: Session):
    """
    Valida o endpoint para um poste que existe mas não tem análises associadas.
    A resposta deve ser bem-sucedida, mas com listas e campos nulos.
    """
    # Arrange
    projeto_id, _ = _seed_database(db_session)

    # Act
    response = client.get(f"/api/projetos/{projeto_id}/postes/P3")

    # Assert
    assert response.status_code == 200
    data = response.json()

    assert data["codigo"] == "P3"
    assert data["resultado_tracao"] is None
    assert data["trechos_conectados"] == []


def test_obter_poste_consolidado_nao_encontrado(db_session: Session):
    """
    Valida que o endpoint retorna 404 Not Found para um poste que não existe no projeto.
    """
    # Arrange
    projeto_id, _ = _seed_database(db_session)

    # Act
    response = client.get(f"/api/projetos/{projeto_id}/postes/P99")

    # Assert
    assert response.status_code == 404
    assert "Poste com código 'P99' não encontrado" in response.json()["detail"]


@pytest.fixture(autouse=True)
def override_dependencies(db_session: Session):
    """Sobrescreve a dependência de sessão para usar o banco de dados de teste."""
    from apps.api.core.deps import get_session_factory

    def get_test_session_factory():
        yield db_session

    app.dependency_overrides[get_session_factory] = get_test_session_factory
    yield
    app.dependency_overrides.clear()