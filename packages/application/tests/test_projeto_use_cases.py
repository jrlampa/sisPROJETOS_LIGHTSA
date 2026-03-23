"""Testes de integracao entre dominio, aplicacao e persistencia local-first."""

from __future__ import annotations

from sqlalchemy import select

from packages.application.use_cases.projeto_use_cases import (
    AvancarEtapaUseCase,
    CriarProjetoUseCase,
)
from packages.domain.workflow.models import EtapaProjeto
from packages.infrastructure.database.models import Base, HistoricoAuditoriaORM, ProjetoORM
from packages.infrastructure.database.session import build_engine, create_session_factory


def criar_dados_projeto() -> dict:
    return {
        "codigo": "ZNA-101",
        "nome": "Projeto Integracao",
        "localidade": "Santa Cruz",
        "checklist_triagem": {
            "tipo_projeto": "Robustez BT",
            "recebeu_leitura_trafo_maxima": True,
            "corrente_trafo_a": 48.7,
            "carga_maxima_transformador_kva": 150.0,
            "possui_fotos_campo": True,
            "comparou_com_street_view": True,
        },
        "evidencias": [
            {
                "tipo": "Foto de Campo",
                "descricao": "Foto da frente do trecho analisado",
                "caminho_arquivo": "levantamento/zna-101/foto-01.jpg",
            }
        ],
    }


def test_criar_projeto_persiste_em_sqlite_memoria() -> None:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = create_session_factory("sqlite+pysqlite:///:memory:", engine=engine)

    use_case = CriarProjetoUseCase(session_factory=session_factory)
    projeto = use_case.executar(criar_dados_projeto())

    with session_factory() as session:
        persistido = session.get(ProjetoORM, str(projeto.id))

    assert projeto.codigo == "ZNA-101"
    assert projeto.etapa_atual is EtapaProjeto.TRIAGEM
    assert persistido is not None
    assert persistido.nome == "Projeto Integracao"


def test_avancar_etapa_registra_historico_no_banco() -> None:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = create_session_factory("sqlite+pysqlite:///:memory:", engine=engine)

    criar_projeto = CriarProjetoUseCase(session_factory=session_factory)
    projeto = criar_projeto.executar(criar_dados_projeto())

    avancar = AvancarEtapaUseCase(session_factory=session_factory)
    projeto_atualizado, historico = avancar.executar(
        projeto_id=projeto.id,
        nova_etapa=EtapaProjeto.CQT,
        responsavel="Equipe Engenharia",
        justificativa="Triagem validada para continuidade.",
    )

    with session_factory() as session:
        registros = session.scalars(select(HistoricoAuditoriaORM)).all()

    assert projeto_atualizado.etapa_atual is EtapaProjeto.CQT
    assert historico.etapa_destino is EtapaProjeto.CQT
    assert len(registros) == 1


def test_falha_ao_pular_etapa_do_fluxo() -> None:
    engine = build_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = create_session_factory("sqlite+pysqlite:///:memory:", engine=engine)

    criar_projeto = CriarProjetoUseCase(session_factory=session_factory)
    projeto = criar_projeto.executar(criar_dados_projeto())

    avancar = AvancarEtapaUseCase(session_factory=session_factory)

    try:
        avancar.executar(
            projeto_id=projeto.id,
            nova_etapa=EtapaProjeto.CAD,
            responsavel="Equipe Engenharia",
        )
    except ValueError as exc:
        assert "Transicao invalida" in str(exc)
    else:
        raise AssertionError("Era esperado erro ao pular etapa do workflow.")
