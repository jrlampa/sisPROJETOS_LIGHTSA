"""Testes unitarios do motor CQT na camada de dominio puro."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from packages.domain.cqt.models import (
    CQTAnalise,
    CentroCarga,
    Condutor,
    TipoRede,
    TrechoEletrico,
    Transformador,
)
from packages.domain.intake.models import TipoProjeto


def _condutor_240_al() -> Condutor:
    return Condutor(nome="240 Al - Arm", resistencia_ohm_km=0.15, ampacidade_a=426)


def _condutor_70_mx() -> Condutor:
    return Condutor(nome="70 Al - MX", resistencia_ohm_km=0.45, ampacidade_a=140)


def test_trecho_calcula_queda_tensao_trifasica() -> None:
    trecho = TrechoEletrico(
        nome="Trecho Trifasico Principal",
        tipo_rede=TipoRede.REDE,
        fases=3,
        comprimento_m=100,
        corrente_a=10,
        tensao_nominal_v=13800,
        condutor=_condutor_240_al(),
    )

    assert trecho.resistencia_total_ohm == pytest.approx(0.015, rel=1e-6)
    assert trecho.queda_tensao_v == pytest.approx(0.2598, rel=1e-3)
    assert trecho.queda_tensao_percent == pytest.approx(0.00188, rel=1e-2)
    assert trecho.dentro_do_limite_qdt is True


def test_trecho_ramal_identifica_excesso_de_qdt() -> None:
    trecho = TrechoEletrico(
        nome="Ramal Critico",
        tipo_rede=TipoRede.RAMAL,
        fases=1,
        comprimento_m=200,
        corrente_a=30,
        tensao_nominal_v=220,
        condutor=_condutor_70_mx(),
    )

    assert trecho.queda_tensao_percent == pytest.approx(1.227, rel=1e-2)
    assert trecho.dentro_do_limite_qdt is True


def test_detecta_erro_02_quando_consumidores_aumentam_a_jusante() -> None:
    trecho = TrechoEletrico(
        nome="Trecho com Inconsistencia",
        tipo_rede=TipoRede.REDE,
        fases=3,
        comprimento_m=80,
        corrente_a=12,
        tensao_nominal_v=13800,
        condutor=_condutor_240_al(),
        consumidores_montante=10,
        consumidores_jusante=12,
    )

    assert trecho.possui_erro_02 is True


def test_cqt_normal_valida_limite_trafo_em_85_percent() -> None:
    centro = CentroCarga(
        nome="CC Normal",
        transformador=Transformador(
            descricao="Trafo 112.5 kVA",
            potencia_nominal_kva=112.5,
            carga_maxima_lida_kva=95,
            corrente_lida_a=380,
        ),
        trechos=(
            TrechoEletrico(
                nome="Trecho Principal",
                tipo_rede=TipoRede.REDE,
                fases=3,
                comprimento_m=100,
                corrente_a=10,
                tensao_nominal_v=13800,
                condutor=_condutor_240_al(),
            ),
        ),
    )

    analise = CQTAnalise(
        tipo_projeto=TipoProjeto.ROBUSTEZ_MT,
        centro_carga=centro,
        recebeu_leitura_trafo_maxima=True,
        corrente_trafo_a=380,
        carga_maxima_transformador_kva=95,
    )

    assert analise.limite_carregamento_trafo_percent == 85.0
    assert analise.trafo_dentro_do_limite is True


def test_cqt_clandestino_exige_campos_especificos() -> None:
    centro = CentroCarga(
        nome="CC Clandestino",
        transformador=Transformador(
            descricao="Trafo 75 kVA",
            potencia_nominal_kva=75,
            carga_maxima_lida_kva=55,
            corrente_lida_a=120,
        ),
        trechos=(
            TrechoEletrico(
                nome="Ramal Clandestino",
                tipo_rede=TipoRede.RAMAL,
                fases=1,
                comprimento_m=60,
                corrente_a=25,
                tensao_nominal_v=220,
                condutor=_condutor_70_mx(),
            ),
        ),
    )

    analise = CQTAnalise(
        tipo_projeto=TipoProjeto.CLANDESTINOS,
        centro_carga=centro,
        recuperacao_clandestino_confirmada=True,
        quantidade_ligacoes_irregulares=3,
    )

    assert analise.limite_carregamento_trafo_percent == 80.0
    assert analise.trafo_dentro_do_limite is True


def test_cqt_clandestino_falha_sem_confirmacao() -> None:
    centro = CentroCarga(
        nome="CC Clandestino",
        transformador=Transformador(
            descricao="Trafo 75 kVA",
            potencia_nominal_kva=75,
            carga_maxima_lida_kva=55,
            corrente_lida_a=120,
        ),
        trechos=(
            TrechoEletrico(
                nome="Ramal Clandestino",
                tipo_rede=TipoRede.RAMAL,
                fases=1,
                comprimento_m=60,
                corrente_a=25,
                tensao_nominal_v=220,
                condutor=_condutor_70_mx(),
            ),
        ),
    )

    with pytest.raises(ValidationError, match="confirmacao de recuperacao"):
        CQTAnalise(
            tipo_projeto=TipoProjeto.CLANDESTINOS,
            centro_carga=centro,
            quantidade_ligacoes_irregulares=3,
        )


def test_cqt_clandestino_falha_com_trafo_acima_de_80_percent() -> None:
    centro = CentroCarga(
        nome="CC Clandestino Critico",
        transformador=Transformador(
            descricao="Trafo 75 kVA",
            potencia_nominal_kva=75,
            carga_maxima_lida_kva=70,
            corrente_lida_a=150,
        ),
        trechos=(
            TrechoEletrico(
                nome="Ramal Clandestino Critico",
                tipo_rede=TipoRede.RAMAL,
                fases=1,
                comprimento_m=80,
                corrente_a=30,
                tensao_nominal_v=220,
                condutor=_condutor_70_mx(),
            ),
        ),
    )

    with pytest.raises(ValidationError, match="Carregamento do transformador excede"):
        CQTAnalise(
            tipo_projeto=TipoProjeto.CLANDESTINOS,
            centro_carga=centro,
            recuperacao_clandestino_confirmada=True,
            quantidade_ligacoes_irregulares=5,
        )
