"""Testes unitarios dos helpers internos do motor legado de tracao."""

from __future__ import annotations

import pytest

from packages.domain.tracao.legacy_engine.plan1_tables import (
    lookup_btzero_qtd_fios,
    lookup_cable_diam,
    lookup_cable_peso,
    lookup_poste_ecc,
    lookup_rede_qtd_cabos,
)
from packages.domain.tracao.legacy_engine.ponto_blocks import (
    BTZeroTraversalInput,
    MTTraversalInput,
    RamaisTraversalInput,
    TraversalCalc,
    _blank,
    _calc_bt_t1_traversal,
    _calc_bt_t2_traversal,
    _calc_mt_traversal,
    _ensure_4,
    _normalize,
    _r,
    _roundup,
    calcular_polo,
)


@pytest.mark.parametrize(
    ("qtd_ligacoes", "qtd_fios"),
    [
        (1, 1),
        (3, 3),
        (8, 5),
        (20, 7),
        (38, 9),
        (61, 11),
    ],
)
def test_lookup_btzero_qtd_fios_respeita_faixas_da_planilha(
    qtd_ligacoes: float, qtd_fios: int
) -> None:
    assert lookup_btzero_qtd_fios(qtd_ligacoes) == qtd_fios


def test_lookups_de_plan1_tratam_encontrado_e_nao_encontrado() -> None:
    assert lookup_cable_diam("397MCM-CA, Nu") == pytest.approx(0.0184)
    assert lookup_cable_peso("397MCM-CA, Nu") == pytest.approx(0.558)
    assert lookup_rede_qtd_cabos("Convencional") == 3
    assert lookup_cable_diam("Cabo inexistente") is None
    assert lookup_poste_ecc("Concreto circular", "11 m / 600 daN") == pytest.approx(20.09)
    assert lookup_poste_ecc("Concreto circular", "modelo inexistente") == 0.0


def test_helpers_de_arredondamento_e_blank_reproduzem_semantica_do_excel() -> None:
    assert _r("texto") == "texto"
    assert _roundup("texto") == "texto"
    assert _roundup(-1.21, 1) == pytest.approx(-1.3)
    assert _blank("sem valor") == " "
    assert _blank(2.0) == 2.0


def test_helpers_de_traversal_tratam_casos_sem_catenaria_ou_sem_mt1() -> None:
    class _ZeroDenominator:
        def __mul__(self, other: float):
            return _AfterFirstSub()

    class _AfterFirstSub:
        def __sub__(self, other: float):
            return _AfterSecondSub()

    class _AfterSecondSub:
        def __sub__(self, other: float):
            return 0.0

    mt_sem_flecha = _calc_mt_traversal(
        tipo_rede="Convencional",
        tipo_cabo="397MCM-CA, Nu",
        vao=20.0,
        flecha=0.0,
        angulo=0.0,
    )
    bt_t1_inativo = _calc_bt_t1_traversal(TraversalCalc(), 0.0, 0.0, 0.0)
    bt_armado_sem_flecha = _calc_bt_t2_traversal(
        tipo_rede="Armado",
        tipo_cabo="Cabo armado 95mm² ",
        vao=18.0,
        flecha=0.0,
        angulo=30.0,
    )

    assert mt_sem_flecha.active is True
    assert mt_sem_flecha.catenary == 0.0
    assert mt_sem_flecha.cat_H == 0.0
    assert mt_sem_flecha.cat_V == 0.0
    assert bt_t1_inativo.active is False
    assert bt_armado_sem_flecha.active is True
    assert bt_armado_sem_flecha.catenary == 0.0
    assert _normalize(resultante=100.0, altura_ancoragem=7.0, altura_poste=_ZeroDenominator()) == 0.0


def test_calcular_polo_cobre_caminhos_sem_mt_com_btz_e_ral_ativos() -> None:
    mt1_inputs: list[MTTraversalInput] = []
    btz_inputs = [
        BTZeroTraversalInput(
            qtd_ligacoes=10,
            vao=20.0,
            flecha=0.8,
            angulo=0.0,
            altura_poste=11.0,
            altura_ancoragem=7.0,
        )
    ]
    ral_inputs = [
        RamaisTraversalInput(
            tipo_cabo="10 mm² - Bipolar",
            qtd_cabos=2,
            vao=18.0,
            flecha=0.7,
            angulo=90.0,
            altura_poste=11.0,
            altura_ancoragem=6.5,
        )
    ]

    _ensure_4(mt1_inputs, MTTraversalInput)

    assert len(mt1_inputs) == 4

    resultado = calcular_polo(
        mt1_inputs=[],
        mt2_inputs=[],
        bt_inputs=[],
        btz_inputs=btz_inputs,
        ral_inputs=ral_inputs,
    )

    assert resultado.mt1.resultante == 0.0
    assert resultado.mt2.resultante == 0.0
    assert resultado.btz.resultante > 0
    assert resultado.ral.resultante > 0
    assert "TRAÇÃO TOTAL" in resultado.texto_total