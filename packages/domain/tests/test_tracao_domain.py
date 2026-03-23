"""Testes unitarios do motor de tracao mecanica na camada de dominio puro."""

from __future__ import annotations

import math

import pytest
from pydantic import ValidationError

from packages.domain.tracao.models import (
    EstadoMecanico,
    NivelTracao,
    Poste,
    ResultadoTracao,
    TraversalFisica,
    Vao,
)

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


def test_poste_estado_reprovado_acima_de_105_percent() -> None:
    """Carregamento acima de 105% da resistencia nominal classifica como REPROVADO."""
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


def test_poste_no_limite_exato_105_percent_nao_reprova() -> None:
    """Carregamento exatamente em 105% deve permanecer fora de REPROVADO."""
    poste = Poste(
        codigo="PE-008B",
        resistencia_nominal_daN=300.0,
        vaos=(_vao(tracao_daN=315.0, azimute_graus=0.0),),
    )

    assert poste.percentual_carregamento == pytest.approx(105.0, rel=1e-6)
    assert poste.estado_mecanico is EstadoMecanico.ALERTA


def test_poste_acima_de_105_percent_reprova() -> None:
    """Carregamento estritamente maior que 105% deve reprovar."""
    poste = Poste(
        codigo="PE-008C",
        resistencia_nominal_daN=300.0,
        vaos=(_vao(tracao_daN=316.0, azimute_graus=0.0),),
    )

    assert poste.percentual_carregamento == pytest.approx(105.333333, rel=1e-6)
    assert poste.estado_mecanico is EstadoMecanico.REPROVADO


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
    assert resultado.percentual_carregamento == pytest.approx(
        poste.percentual_carregamento, rel=1e-9
    )
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


# ---------------------------------------------------------------------------
# Motor Fisico — Cosmo LDA (valores de ouro confirmados no workbook LIGHT)
# ---------------------------------------------------------------------------
#
# Poste Cosmo LDA / 11 m 600 daN — configuracao real documentada em
# docs/LEGACY_ANALYSIS_TRACAO.md.  Resultados esperados (workbook Excel):
#   MT1 = 217.37 daN @ 177°  |  MT2 = 171.33 daN @ 90°
#   BT  = 165.39 daN @  60°  |  TOTAL = 373.67 daN @ 112°  ECC = 20.09 daN
# ---------------------------------------------------------------------------


def _cosmo_lda_traversals() -> tuple[TraversalFisica, ...]:
    """Devolve as traversals fisicas do poste Cosmo LDA (caso de ouro)."""
    return (
        # MT1 — T1
        TraversalFisica(
            nivel=NivelTracao.MT1,
            posicao=1,
            tipo_rede="Convencional",
            tipo_cabo="397MCM-CA, Nu",
            vao_m=33.0,
            flecha_m=0.5,
            angulo_graus=0.0,
            altura_poste_m=11.0,
            altura_ancoragem_m=9.2,
        ),
        # MT1 — T2
        TraversalFisica(
            nivel=NivelTracao.MT1,
            posicao=2,
            tipo_rede="Convencional",
            tipo_cabo="397MCM-CA, Nu",
            vao_m=40.0,
            flecha_m=0.5,
            angulo_graus=179.0,
            altura_poste_m=11.0,
            altura_ancoragem_m=9.2,
        ),
        # MT2 — T1
        TraversalFisica(
            nivel=NivelTracao.MT2,
            posicao=1,
            tipo_rede="Compacta",
            tipo_cabo="397MCM-CA, XLPE, 13,8 kV",
            vao_m=27.0,
            flecha_m=0.5,
            angulo_graus=11.0,
            altura_poste_m=11.0,
            altura_ancoragem_m=8.2,
        ),
        # MT2 — T2
        TraversalFisica(
            nivel=NivelTracao.MT2,
            posicao=2,
            tipo_rede="Compacta",
            tipo_cabo="397MCM-CA, XLPE, 13,8 kV",
            vao_m=27.0,
            flecha_m=0.5,
            angulo_graus=169.0,
            altura_poste_m=11.0,
            altura_ancoragem_m=8.2,
        ),
        # BT — T1 (geometria herdada do MT1 T1)
        TraversalFisica(
            nivel=NivelTracao.BT,
            posicao=1,
            tipo_rede="Multiplexada",
            tipo_cabo="70mm\u00b2, MTX-BT ",
            altura_ancoragem_m=7.0,
        ),
        # BT — T2 (geometria herdada do MT1 T2)
        TraversalFisica(
            nivel=NivelTracao.BT,
            posicao=2,
            tipo_rede="Multiplexada",
            tipo_cabo="70mm\u00b2, MTX-BT ",
            altura_ancoragem_m=7.0,
        ),
        # BT — T3 (vao independente)
        TraversalFisica(
            nivel=NivelTracao.BT,
            posicao=3,
            tipo_rede="Multiplexada",
            tipo_cabo="70mm\u00b2, MTX-BT ",
            vao_m=20.0,
            flecha_m=0.5,
            angulo_graus=85.0,
            altura_poste_m=11.0,
            altura_ancoragem_m=7.0,
        ),
    )


def test_motor_fisico_cosmo_lda_total_tracao() -> None:
    """Motor fisico deve reproduzir o valor de ouro do workbook: 373.67 daN."""
    poste = Poste(
        codigo="COSMO-LDA",
        resistencia_nominal_daN=600.0,
        traversals_fisicas=_cosmo_lda_traversals(),
        tipo_poste="Concreto circular",
        modelo_poste="11 m / 600 daN",
    )

    assert poste.esforco_resultante_daN == pytest.approx(373.67, abs=0.5)


def test_motor_fisico_cosmo_lda_estado_aprovado() -> None:
    """373.67 / 600 = 62.3 % -> estado APROVADO (abaixo de 80%)."""
    poste = Poste(
        codigo="COSMO-LDA",
        resistencia_nominal_daN=600.0,
        traversals_fisicas=_cosmo_lda_traversals(),
        tipo_poste="Concreto circular",
        modelo_poste="11 m / 600 daN",
    )

    assert poste.estado_mecanico is EstadoMecanico.APROVADO


def test_motor_fisico_resultado_tracao_agrega_motor_legado() -> None:
    """ResultadoTracao.calcular() deve funcionar quando alimentado pelo motor fisico."""
    poste = Poste(
        codigo="COSMO-LDA",
        resistencia_nominal_daN=600.0,
        traversals_fisicas=_cosmo_lda_traversals(),
        tipo_poste="Concreto circular",
        modelo_poste="11 m / 600 daN",
    )

    resultado = ResultadoTracao.calcular(poste)

    assert resultado.esforco_resultante_daN == pytest.approx(373.67, abs=0.5)
    assert resultado.estado_mecanico is EstadoMecanico.APROVADO


def test_motor_fisico_poste_sem_traversals_usa_fallback() -> None:
    """Poste sem traversals_fisicas deve continuar usando a soma vetorial simples."""
    poste = Poste(
        codigo="PE-FALLBACK",
        resistencia_nominal_daN=300.0,
        vaos=(_vao(tracao_daN=200.0, azimute_graus=0.0),),
    )

    assert poste.esforco_resultante_daN == pytest.approx(200.0, rel=1e-6)


def test_motor_fisico_traversal_sem_vao_requer_apenas_ancoragem() -> None:
    """TraversalFisica sem vao_m e valida; vao_m fica em 0.0 (geometria herdada de MT1)."""
    t = TraversalFisica(
        nivel=NivelTracao.BT,
        posicao=1,
        tipo_rede="Multiplexada",
        tipo_cabo="70mm\u00b2, MTX-BT ",
        altura_ancoragem_m=7.0,
    )
    assert t.vao_m == 0.0  # sentinela: geometria herdada do nivel MT1
    assert t.flecha_m == 0.0


def test_motor_fisico_traversal_com_vao_exige_flecha() -> None:
    """TraversalFisica com vao_m deve exigir flecha_m."""
    with pytest.raises(ValidationError):
        TraversalFisica(
            nivel=NivelTracao.BT,
            posicao=1,
            tipo_rede="Multiplexada",
            tipo_cabo="70mm\u00b2, MTX-BT ",
            vao_m=20.0,
            # flecha_m ausente — deve reprovar
            angulo_graus=85.0,
            altura_poste_m=11.0,
            altura_ancoragem_m=7.0,
        )


def test_motor_fisico_com_btz_e_ral_aciona_agrupamento_do_helper() -> None:
    poste = Poste(
        codigo="PE-BTZ-RAL",
        resistencia_nominal_daN=300.0,
        traversals_fisicas=(
            TraversalFisica(
                nivel=NivelTracao.BTZ,
                posicao=1,
                qtd_ligacoes=6,
                vao_m=20.0,
                flecha_m=0.8,
                angulo_graus=0.0,
                altura_poste_m=11.0,
                altura_ancoragem_m=7.0,
            ),
            TraversalFisica(
                nivel=NivelTracao.RAL,
                posicao=1,
                tipo_cabo="10 mm² - Bipolar",
                qtd_cabos=2,
                vao_m=18.0,
                flecha_m=0.7,
                angulo_graus=90.0,
                altura_poste_m=11.0,
                altura_ancoragem_m=6.5,
            ),
        ),
    )

    assert poste.esforco_resultante_daN > 0
    assert poste.percentual_carregamento > 0
