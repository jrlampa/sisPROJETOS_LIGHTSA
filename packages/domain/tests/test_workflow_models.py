"""Testes das entidades de workflow e governanca."""

import uuid

import pytest
from pydantic import ValidationError

from packages.domain.workflow.models import EtapaProjeto, HistoricoAuditoria


def test_cria_historico_auditoria_valido() -> None:
    historico = HistoricoAuditoria(
        projeto_id=uuid.uuid4(),
        etapa_origem=EtapaProjeto.TRIAGEM,
        etapa_destino=EtapaProjeto.CQT,
        acao="Avanco para analise CQT",
        responsavel="Engenharia LIGHT",
    )

    assert historico.etapa_destino is EtapaProjeto.CQT


def test_falha_quando_etapa_origem_e_destino_sao_iguais() -> None:
    with pytest.raises(ValidationError, match="origem deve ser diferente"):
        HistoricoAuditoria(
            projeto_id=uuid.uuid4(),
            etapa_origem=EtapaProjeto.CAD,
            etapa_destino=EtapaProjeto.CAD,
            acao="Tentativa de transicao invalida",
            responsavel="Equipe QA",
        )