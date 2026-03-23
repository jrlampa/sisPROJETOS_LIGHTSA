"""Testes de integracao do caso de uso de analise CQT."""

from __future__ import annotations

from uuid import UUID

import pytest
from pydantic import ValidationError
from sqlalchemy import select

from packages.application.use_cases.cqt_use_cases import ExecutarAnaliseCQTUseCase
from packages.application.use_cases.projeto_use_cases import CriarProjetoUseCase
from packages.infrastructure.database.models import (
    Base,
    CentroCargaORM,
    CQTAnaliseORM,
    TransformadorORM,
    TrechoEletricoORM,
)
from packages.infrastructure.database.session import build_engine, create_session_factory


def _setup_in_memory_session_factory():
    engine = build_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return create_session_factory("sqlite+pysqlite:///:memory:", engine=engine)


def _dados_projeto() -> dict:
    return {
        "codigo": "ZNA-CQT-001",
        "nome": "Projeto para CQT",
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
                "caminho_arquivo": "campo/projeto-cqt-001.jpg",
            }
        ],
    }


def _dados_cqt_normal() -> dict:
    return {
        "tipo_projeto": "Robustez BT",
        "recebeu_leitura_trafo_maxima": True,
        "corrente_trafo_a": 110.0,
        "carga_maxima_transformador_kva": 75.0,
        "centro_carga": {
            "nome": "CC-001",
            "transformador": {
                "descricao": "Trafo BT 112.5",
                "potencia_nominal_kva": 112.5,
                "carga_maxima_lida_kva": 75.0,
                "corrente_lida_a": 110.0,
            },
            "trechos": [
                {
                    "nome": "Trecho Principal",
                    "tipo_rede": "rede",
                    "fases": 3,
                    "comprimento_m": 120.0,
                    "corrente_a": 35.0,
                    "tensao_nominal_v": 13800.0,
                    "ordem_no_circuito": 1,
                    "consumidores_montante": 20,
                    "consumidores_jusante": 15,
                    "fases_montante": 3,
                    "fases_jusante": 3,
                    "condutor": {
                        "nome": "240 Al - Arm",
                        "resistencia_ohm_km": 0.15,
                        "ampacidade_a": 426.0,
                    },
                },
                {
                    "nome": "Ramal Secundario",
                    "tipo_rede": "ramal",
                    "fases": 1,
                    "comprimento_m": 50.0,
                    "corrente_a": 20.0,
                    "tensao_nominal_v": 220.0,
                    "ordem_no_circuito": 2,
                    "consumidores_montante": 15,
                    "consumidores_jusante": 10,
                    "fases_montante": 1,
                    "fases_jusante": 1,
                    "condutor": {
                        "nome": "70 Al - MX",
                        "resistencia_ohm_km": 0.45,
                        "ampacidade_a": 140.0,
                    },
                },
            ],
        },
    }


def test_executar_analise_cqt_salva_golden_case_no_sqlite() -> None:
    session_factory = _setup_in_memory_session_factory()

    criar_projeto = CriarProjetoUseCase(session_factory=session_factory)
    projeto = criar_projeto.executar(_dados_projeto())

    use_case = ExecutarAnaliseCQTUseCase(session_factory=session_factory)
    analise = use_case.executar(projeto.id, _dados_cqt_normal())

    with session_factory() as session:
        cqt = session.scalars(select(CQTAnaliseORM)).all()
        centros = session.scalars(select(CentroCargaORM)).all()
        trafos = session.scalars(select(TransformadorORM)).all()
        trechos = session.scalars(select(TrechoEletricoORM)).all()

    assert analise.qdt_total_dentro_do_limite is True
    assert analise.trafo_dentro_do_limite is True
    assert len(cqt) == 1
    assert len(centros) == 1
    assert len(trafos) == 1
    assert len(trechos) == 2


def test_executar_analise_cqt_falha_para_projeto_inexistente() -> None:
    session_factory = _setup_in_memory_session_factory()
    use_case = ExecutarAnaliseCQTUseCase(session_factory=session_factory)

    with pytest.raises(ValueError, match="Projeto nao encontrado"):
        use_case.executar(UUID("11111111-1111-1111-1111-111111111111"), _dados_cqt_normal())


def test_executar_analise_cqt_falha_em_regra_clandestino() -> None:
    session_factory = _setup_in_memory_session_factory()
    criar_projeto = CriarProjetoUseCase(session_factory=session_factory)
    projeto = criar_projeto.executar(_dados_projeto())

    payload = _dados_cqt_normal()
    payload["tipo_projeto"] = "Clandestinos"
    payload["recuperacao_clandestino_confirmada"] = None
    payload["quantidade_ligacoes_irregulares"] = 4
    payload["recebeu_leitura_trafo_maxima"] = False
    payload["corrente_trafo_a"] = None
    payload["carga_maxima_transformador_kva"] = None

    use_case = ExecutarAnaliseCQTUseCase(session_factory=session_factory)
    with pytest.raises(ValidationError, match="confirmacao de recuperacao"):
        use_case.executar(projeto.id, payload)
