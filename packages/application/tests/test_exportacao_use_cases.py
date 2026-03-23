"""Testes de integracao do caso de uso de geracao do pacote final."""

from __future__ import annotations

import shutil
from pathlib import Path

from sqlalchemy import select

from packages.application.use_cases.cqt_use_cases import ExecutarAnaliseCQTUseCase
from packages.application.use_cases.exportacao_use_cases import GerarPacoteFinalUseCase
from packages.application.use_cases.projeto_use_cases import CriarProjetoUseCase
from packages.application.use_cases.tracao_use_cases import CalcularTracaoProjetoUseCase
from packages.infrastructure.database.models import Base, PacoteEntregaORM
from packages.infrastructure.database.session import build_engine, create_session_factory


def _setup_in_memory_session_factory():
    engine = build_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return create_session_factory("sqlite+pysqlite:///:memory:", engine=engine)


def _dados_projeto() -> dict:
    return {
        "codigo": "ZNA-EXP-001",
        "nome": "Projeto para Exportacao",
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
                "caminho_arquivo": "campo/projeto-exp-001.jpg",
            }
        ],
    }


def _dados_cqt() -> dict:
    return {
        "tipo_projeto": "Robustez BT",
        "recebeu_leitura_trafo_maxima": True,
        "corrente_trafo_a": 110.0,
        "carga_maxima_transformador_kva": 75.0,
        "centro_carga": {
            "nome": "CC-EXP",
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
                }
            ],
        },
    }


def _dados_tracao() -> list[dict]:
    return [
        {
            "codigo": "PE-EXP-001",
            "resistencia_nominal_daN": 300.0,
            "vaos": [
                {
                    "comprimento_m": 80.0,
                    "tipo_cabo": "CAA 70mm2",
                    "tracao_daN": 200.0,
                    "azimute_graus": 0.0,
                }
            ],
        }
    ]


def test_gerar_pacote_final_cria_zip_e_persiste_status_concluido() -> None:
    session_factory = _setup_in_memory_session_factory()

    projeto = CriarProjetoUseCase(session_factory=session_factory).executar(_dados_projeto())
    ExecutarAnaliseCQTUseCase(session_factory=session_factory).executar(projeto.id, _dados_cqt())
    CalcularTracaoProjetoUseCase(session_factory=session_factory).executar(projeto.id, _dados_tracao())

    pacote = GerarPacoteFinalUseCase(session_factory=session_factory).executar(projeto.id)

    caminho_zip = Path(pacote.caminho_arquivo or "")
    try:
        assert pacote.status.value == "CONCLUIDO"
        assert caminho_zip.exists()
        assert caminho_zip.suffix.lower() == ".zip"

        with session_factory() as session:
            registro = session.scalars(select(PacoteEntregaORM)).one_or_none()

        assert registro is not None
        assert registro.status == "CONCLUIDO"
        assert registro.caminho_arquivo == str(caminho_zip)
    finally:
        if caminho_zip.exists():
            shutil.rmtree(caminho_zip.parent, ignore_errors=True)
