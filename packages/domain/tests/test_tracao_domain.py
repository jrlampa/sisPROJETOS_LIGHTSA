"""Testes unitarios do motor de tracao mecanica na camada de dominio puro."""

from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from packages.domain.tracao.models import EstadoMecanico, Poste, ResultadoTracao, Vao


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------


def _vao(
    tracao_daN: float,
    azimute_graus: float,
    comprimento_m: float = 80.0,
    tipo_cabo: str = "CAA 70mm2",
) -> Vao:
    return Vao(
        comprimento_m=comprimento_m,
        tipo_cabo=tipo_cabo,
        tracao_daN=tracao_daN,
        azimute_graus=azimute_graus,
    )


# ---------------------------------------------------------------------------
# Poste — casos de calculo fisico
# ---------------------------------------------------------------------------


def test_poste_fim_de_linha_resultante_igual_a_tracao() -> None:
    """Fim de linha com um vao: resultante deve ser igual a tracao do vao."""
    poste = Poste(
        codigo="PE-001",
        resistencia_nominal_daN=300.0,
        vaos=(_vao(tracao_daN=200.0, azimute_graus=0.0),),
    )

    assert poste.esforco_resultante_daN == pytest.approx(200.0, rel=1e-6)
    assert poste.percentual_carregamento == pytest.approx(66.67, rel=1e-2)
    assert poste.estado_mecanico is EstadoMecanico.APROVADO


def test_poste_passagem_equilibrado_forcas_se_anulam() -> None:
    """Passagem com tracao igual em vaos opostos: resultante aproxima zero."""
    poste = Poste(
        codigo="PE-002",
        resistencia_nominal_daN=300.0,
        vaos=(
            _vao(tracao_daN=200.0, azimute_graus=0.0),
            _vao(tracao_daN=200.0, azimute_graus=180.0),
        ),
    )

    assert poste.esforco_resultante_daN == pytest.approx(0.0, abs=1e-9)
    assert poste.percentual_carregamento == pytest.approx(0.0, abs=1e-6)
    assert poste.estado_mecanico is EstadoMecanico.APROVADO


def test_poste_passagem_desequilibrado_resultante_e_diferenca() -> None:
    """Passagem assimetrica: resultante equivale a diferenca entre as tracoes opostas."""
    poste = Poste(
        codigo="PE-003",
        resistencia_nominal_daN=300.0,
        vaos=(
            _vao(tracao_daN=250.0, azimute_graus=0.0, comprimento_m=100.0),
            _vao(tracao_daN=50.0, azimute_graus=180.0, comprimento_m=60.0),
        ),
    )

    assert poste.esforco_resultante_daN == pytest.approx(200.0, rel=1e-6)
    assert poste.estado_mecanico is EstadoMecanico.APROVADO


def test_poste_angulo_reto_resultante_vetorial() -> None:
    """Poste de angulo reto com tracoes iguais: resultante = T * sqrt(2)."""
    poste = Poste(
        codigo="PE-004",
        resistencia_nominal_daN=600.0,
        vaos=(
            _vao(tracao_daN=200.0, azimute_graus=0.0),
            _vao(tracao_daN=200.0, azimute_graus=90.0),
        ),
    )

    assert poste.esforco_resultante_daN == pytest.approx(200.0 * math.sqrt(2), rel=1e-6)
    # 282.8 / 600 = ~47.1% -> APROVADO
    assert poste.estado_mecanico is EstadoMecanico.APROVADO


# ---------------------------------------------------------------------------
# Poste — estados mecanicos
# ---------------------------------------------------------------------------


def test_poste_estado_alerta_entre_80_e_100_percent() -> None:
    """Carregamento entre 80% e 100% classifica o poste como ALERTA."""
    poste = Poste(
        codigo="PE-005",
        resistencia_nominal_daN=300.0,
        vaos=(_vao(tracao_daN=270.0, azimute_graus=0.0),),
    )

    assert poste.percentual_carregamento == pytest.approx(90.0, rel=1e-4)
    assert poste.estado_mecanico is EstadoMecanico.ALERTA


def test_poste_estado_reprovado_acima_de_100_percent() -> None:
    """Carregamento acima da resistencia nominal classifica o poste como REPROVADO."""
    poste = Poste(
        codigo="PE-006",
        resistencia_nominal_daN=300.0,
        vaos=(_vao(tracao_daN=350.0, azimute_graus=0.0),),
    )

    assert poste.percentual_carregamento == pytest.approx(116.67, rel=1e-2)
    assert poste.estado_mecanico is EstadoMecanico.REPROVADO


def test_poste_no_limite_exato_80_percent_e_aprovado() -> None:
    """Carregamento exatamente em 80% deve ser classificado como APROVADO."""
    poste = Poste(
        codigo="PE-007",
        resistencia_nominal_daN=300.0,
        vaos=(_vao(tracao_daN=240.0, azimute_graus=0.0),),  # 240/300 = 80%
    )

    assert poste.percentual_carregamento == pytest.approx(80.0, rel=1e-6)
    assert poste.estado_mecanico is EstadoMecanico.APROVADO


def test_poste_no_limite_exato_100_percent_e_alerta() -> None:
    """Carregamento exatamente em 100% deve ser classificado como ALERTA."""
    poste = Poste(
        codigo="PE-008",
        resistencia_nominal_daN=300.0,
        vaos=(_vao(tracao_daN=300.0, azimute_graus=0.0),),  # 300/300 = 100%
    )

    assert poste.percentual_carregamento == pytest.approx(100.0, rel=1e-6)
    assert poste.estado_mecanico is EstadoMecanico.ALERTA


# ---------------------------------------------------------------------------
# ResultadoTracao
# ---------------------------------------------------------------------------


def test_resultado_tracao_agrega_dados_do_poste() -> None:
    """ResultadoTracao.calcular() deve espelhar todos os campos do Poste."""
    poste = Poste(
        codigo="PE-009",
        resistencia_nominal_daN=500.0,
        vaos=(_vao(tracao_daN=300.0, azimute_graus=0.0),),
    )

    resultado = ResultadoTracao.calcular(poste)

    assert resultado.poste is poste
    assert resultado.esforco_resultante_daN == pytest.approx(poste.esforco_resultante_daN, rel=1e-9)
    assert resultado.percentual_carregamento == pytest.approx(poste.percentual_carregamento, rel=1e-9)
    assert resultado.estado_mecanico is poste.estado_mecanico
    assert resultado.calculado_em is not None


def test_resultado_tracao_reprovado_persiste_estado() -> None:
    """ResultadoTracao registra corretamente um poste reprovado."""
    poste = Poste(
        codigo="PE-010",
        resistencia_nominal_daN=200.0,
        vaos=(_vao(tracao_daN=300.0, azimute_graus=45.0),),
    )

    resultado = ResultadoTracao.calcular(poste)

    assert resultado.estado_mecanico is EstadoMecanico.REPROVADO


# ---------------------------------------------------------------------------
# Validacoes de entrada
# ---------------------------------------------------------------------------


def test_vao_rejeita_tracao_negativa() -> None:
    """Vao nao aceita tracao zero ou negativa."""
    with pytest.raises(ValidationError):
        Vao(comprimento_m=80.0, tipo_cabo="CAA 70mm2", tracao_daN=-10.0, azimute_graus=0.0)


def test_vao_rejeita_azimute_fora_de_intervalo() -> None:
    """Vao rejeita azimute >= 360 graus."""
    with pytest.raises(ValidationError):
        Vao(comprimento_m=80.0, tipo_cabo="CAA 70mm2", tracao_daN=100.0, azimute_graus=360.0)


def test_poste_rejeita_resistencia_nominal_zero() -> None:
    """Poste nao aceita resistencia nominal zero ou negativa."""
    with pytest.raises(ValidationError):
        Poste(codigo="PE-ERR", resistencia_nominal_daN=0.0, vaos=())


def test_poste_e_imutavel() -> None:
    """Poste nao aceita modificacao apos criacao (frozen=True)."""
    poste = Poste(
        codigo="PE-011",
        resistencia_nominal_daN=300.0,
        vaos=(),
    )
    with pytest.raises(Exception):
        poste.codigo = "PE-MOD"  # type: ignore[misc]
