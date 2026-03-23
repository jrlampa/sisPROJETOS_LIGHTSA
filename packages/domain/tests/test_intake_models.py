"""Testes das entidades de intake e triagem."""

import pytest
from pydantic import ValidationError

from packages.domain.intake.models import (
    ChecklistTriagem,
    Evidencia,
    Projeto,
    TipoEvidencia,
    TipoProjeto,
)


def test_cria_checklist_clandestino_com_campos_obrigatorios() -> None:
    checklist = ChecklistTriagem(
        tipo_projeto=TipoProjeto.CLANDESTINOS,
        recuperacao_clandestino_confirmada=True,
        quantidade_ligacoes_irregulares=4,
        possui_fotos_campo=True,
        comparou_com_street_view=True,
    )

    assert checklist.exige_cqt_clandestino is True
    assert checklist.quantidade_ligacoes_irregulares == 4


def test_falha_quando_clandestino_nao_informa_campos_especificos() -> None:
    with pytest.raises(ValidationError, match="confirmacao de recuperacao de clandestino"):
        ChecklistTriagem(tipo_projeto=TipoProjeto.CLANDESTINOS)


def test_falha_quando_clandestino_nao_informa_quantidade_irregular() -> None:
    with pytest.raises(ValidationError, match="quantidade de ligacoes irregulares"):
        ChecklistTriagem(
            tipo_projeto=TipoProjeto.CLANDESTINOS,
            recuperacao_clandestino_confirmada=True,
        )


def test_falha_quando_clandestino_usa_flag_de_leitura_maxima() -> None:
    with pytest.raises(ValidationError, match="nao deve depender da flag de leitura maxima"):
        ChecklistTriagem(
            tipo_projeto=TipoProjeto.CLANDESTINOS,
            recuperacao_clandestino_confirmada=True,
            quantidade_ligacoes_irregulares=2,
            recebeu_leitura_trafo_maxima=True,
        )


def test_falha_quando_projeto_nao_clandestino_tem_leitura_sem_valores_do_trafo() -> None:
    with pytest.raises(ValidationError, match="corrente e carga maxima"):
        ChecklistTriagem(
            tipo_projeto=TipoProjeto.ROBUSTEZ_BT,
            recebeu_leitura_trafo_maxima=True,
        )


def test_falha_quando_projeto_nao_clandestino_recebe_confirmacao_de_clandestino() -> None:
    with pytest.raises(ValidationError, match="Campos especificos de clandestino"):
        ChecklistTriagem(
            tipo_projeto=TipoProjeto.ROBUSTEZ_BT,
            recuperacao_clandestino_confirmada=True,
        )


def test_falha_quando_projeto_nao_clandestino_recebe_quantidade_irregular() -> None:
    with pytest.raises(ValidationError, match="Quantidade de ligacoes irregulares"):
        ChecklistTriagem(
            tipo_projeto=TipoProjeto.ROBUSTEZ_BT,
            quantidade_ligacoes_irregulares=1,
        )


def test_falha_quando_tipo_de_projeto_e_invalido() -> None:
    with pytest.raises(ValidationError):
        ChecklistTriagem(tipo_projeto="Projeto Invalido")


def test_falha_quando_evidencia_nao_informa_origem() -> None:
    with pytest.raises(ValidationError, match="caminho de arquivo ou uma URL"):
        Evidencia(tipo=TipoEvidencia.FOTO_CAMPO, descricao="Foto do poste")


def test_cria_projeto_com_evidencias() -> None:
    checklist = ChecklistTriagem(
        tipo_projeto=TipoProjeto.LIGACAO_NOVA,
        recebeu_leitura_trafo_maxima=True,
        corrente_trafo_a=32.5,
        carga_maxima_transformador_kva=112.4,
        possui_fotos_campo=True,
    )
    evidencia = Evidencia(
        tipo=TipoEvidencia.FOTO_CAMPO,
        descricao="Foto frontal da rede existente",
        caminho_arquivo="levantamentos/projeto-001/foto-01.jpg",
    )

    projeto = Projeto(
        codigo="ZNA-001",
        nome="Projeto piloto",
        localidade="Bangu",
        checklist_triagem=checklist,
        evidencias=(evidencia,),
    )

    assert projeto.checklist_triagem.tipo_projeto is TipoProjeto.LIGACAO_NOVA
    assert len(projeto.evidencias) == 1
