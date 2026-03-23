"""Testes de integracao do caso de uso de tracao poste a poste."""

from __future__ import annotations

import pytest
from sqlalchemy import select

from packages.application.use_cases.projeto_use_cases import CriarProjetoUseCase
from packages.application.use_cases.tracao_use_cases import CalcularTracaoProjetoUseCase
from packages.infrastructure.database.models import Base, PosteTracaoORM, ResultadoTracaoORM
from packages.infrastructure.database.session import build_engine, create_session_factory


def _setup_in_memory_session_factory():
    engine = build_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return create_session_factory("sqlite+pysqlite:///:memory:", engine=engine)


def _dados_projeto() -> dict:
    return {
        "codigo": "ZNA-TRACAO-001",
        "nome": "Projeto para Tracao",
        "localidade": "Campo Grande",
        "checklist_triagem": {
            "tipo_projeto": "Robustez BT",
            "recebeu_leitura_trafo_maxima": True,
            "corrente_trafo_a": 110.0,
            "carga_maxima_transformador_kva": 75.0,
            "possui_fotos_campo": True,
        },
        "evidencias": [
            {
                "tipo": "Foto de Campo",
                "descricao": "Foto inicial",
                "caminho_arquivo": "campo/projeto-tracao-001.jpg",
            }
        ],
    }


def _postes_golden_case() -> list[dict]:
    return [
        {
            "codigo": "PE-TRC-001",
            "resistencia_nominal_daN": 300.0,
            "vaos": [
                {
                    "comprimento_m": 80.0,
                    "tipo_cabo": "CAA 70mm2",
                    "tracao_daN": 200.0,
                    "azimute_graus": 0.0,
                }
            ],
        },
        {
            "codigo": "PE-TRC-002",
            "resistencia_nominal_daN": 300.0,
            "vaos": [
                {
                    "comprimento_m": 75.0,
                    "tipo_cabo": "CAA 70mm2",
                    "tracao_daN": 200.0,
                    "azimute_graus": 0.0,
                },
                {
                    "comprimento_m": 75.0,
                    "tipo_cabo": "CAA 70mm2",
                    "tracao_daN": 200.0,
                    "azimute_graus": 180.0,
                },
            ],
        },
        {
            "codigo": "PE-TRC-003",
            "resistencia_nominal_daN": 300.0,
            "vaos": [
                {
                    "comprimento_m": 90.0,
                    "tipo_cabo": "CAA 70mm2",
                    "tracao_daN": 350.0,
                    "azimute_graus": 0.0,
                }
            ],
        },
    ]


def test_calcular_tracao_projeto_persiste_tres_postes_e_resultados() -> None:
    session_factory = _setup_in_memory_session_factory()

    criar_projeto = CriarProjetoUseCase(session_factory=session_factory)
    projeto = criar_projeto.executar(_dados_projeto())

    use_case = CalcularTracaoProjetoUseCase(session_factory=session_factory)
    resultados = use_case.executar(projeto.id, _postes_golden_case())

    assert len(resultados) == 3
    assert resultados[0].estado_mecanico.value == "APROVADO"
    assert resultados[1].estado_mecanico.value == "APROVADO"
    assert resultados[2].estado_mecanico.value == "REPROVADO"

    with session_factory() as session:
        postes = session.scalars(select(PosteTracaoORM).order_by(PosteTracaoORM.codigo)).all()
        persisted = (
            session.scalars(select(ResultadoTracaoORM).join(PosteTracaoORM).order_by(PosteTracaoORM.codigo)).all()
        )

    assert len(postes) == 3
    assert len(persisted) == 3

    # Cada poste deve manter os vaos originais em JSON para replay de calculo.
    assert len(postes[0].vaos_json) == 1
    assert len(postes[1].vaos_json) == 2
    assert len(postes[2].vaos_json) == 1

    assert persisted[0].estado_mecanico == "APROVADO"
    assert persisted[0].esforco_resultante_daN == pytest.approx(200.0, rel=1e-6)

    assert persisted[1].estado_mecanico == "APROVADO"
    assert persisted[1].esforco_resultante_daN == pytest.approx(0.0, abs=1e-9)

    assert persisted[2].estado_mecanico == "REPROVADO"
    assert persisted[2].percentual_carregamento == pytest.approx(116.67, rel=1e-2)
