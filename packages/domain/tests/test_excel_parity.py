"""Paridade de calculo entre backend e workbooks Excel legados LIGHT."""

from __future__ import annotations

import math
from pathlib import Path

from packages.domain.cqt.models import CQTAnalise
from packages.domain.tests.excel_parity_support import (
    extract_cqt,
    extract_tracao,
    find_sheet_with_keywords,
    load_workbook_or_skip,
)
from packages.domain.tracao.legacy_engine.ponto_blocks import calcular_polo

CQT_EXCEL_PATH = Path(
    r"C:\Users\jonat\OneDrive - IM3 Brasil\LIGHT\PROJETOS\REDE CLANDESTINA - RUAS JERUSALÉM E UVA - SANTA CRUZ RJ\QDT ZNA PROJETADA 1 - RUA JERUSALEM.xlsm"
)
TRACAO_EXCEL_PATH = Path(
    r"C:\Users\jonat\OneDrive - IM3 Brasil\LIGHT\PROJETOS\REDE CLANDESTINA - RUAS JERUSALÉM E UVA - SANTA CRUZ RJ\CALC TRAÇÃO\PROJETO I - RUA JERUSALÉM\CLANDESTINO - RUA JERUSALÉM - PROJETO I - POSTE 2.xlsm"
)
MAX_DIVERGENCIA_PERCENT = 0.01
REL_TOL = 0.0001


def _assert_close_rel_percent(actual: float, expected: float, label: str) -> None:
    is_close = math.isclose(actual, expected, rel_tol=REL_TOL, abs_tol=0.0)
    diff_percent = (abs(actual - expected) / max(abs(expected), 1e-12)) * 100
    assert is_close, (
        f"Divergencia acima da tolerancia em {label}: "
        f"actual={actual:.10f}, expected={expected:.10f}, diff%={diff_percent:.10f}, "
        f"tol_rel={REL_TOL} (~{MAX_DIVERGENCIA_PERCENT}%)"
    )


def test_excel_parity_cqt_e_tracao() -> None:
    wb_cqt, temp_cqt = load_workbook_or_skip(CQT_EXCEL_PATH)
    wb_tracao, temp_tracao = load_workbook_or_skip(TRACAO_EXCEL_PATH)

    try:
        ws_cqt = find_sheet_with_keywords(wb_cqt, "Trecho do Circuito", "Queda")
        if ws_cqt is None:
            raise AssertionError("Nao foi encontrada aba de CQT na planilha fornecida.")

        cqt = extract_cqt(ws_cqt)
        analise = CQTAnalise.model_validate(cqt.payload)
        _assert_close_rel_percent(
            actual=analise.centro_carga.queda_total_percent,
            expected=cqt.expected_queda_total_percent,
            label="CQT.queda_total_percent",
        )

        ws_tracao = find_sheet_with_keywords(wb_tracao, "TRACAO TOTAL")
        if ws_tracao is None:
            raise AssertionError("Nao foi encontrada aba de Tracao no workbook de referencia.")

        tracao = extract_tracao(ws_tracao)
        out = calcular_polo(
            mt1_inputs=tracao.mt1,
            mt2_inputs=tracao.mt2,
            bt_inputs=tracao.bt,
            btz_inputs=tracao.btz,
            ral_inputs=tracao.ral,
            tipo_poste=tracao.tipo_poste,
            modelo_poste=tracao.modelo_poste,
        )

        _assert_close_rel_percent(
            actual=out.total_tracao,
            expected=tracao.expected_total_tracao,
            label="TRACAO.total_tracao",
        )
        _assert_close_rel_percent(
            actual=out.total_angulo,
            expected=tracao.expected_total_angulo,
            label="TRACAO.total_angulo",
        )

        # Momentos/resultantes visiveis para QA eletrica (componentes vetoriais do total)
        expected_mx = tracao.expected_total_tracao * math.cos(
            math.radians(tracao.expected_total_angulo)
        )
        expected_my = tracao.expected_total_tracao * math.sin(
            math.radians(tracao.expected_total_angulo)
        )
        actual_mx = out.total_tracao * math.cos(math.radians(out.total_angulo))
        actual_my = out.total_tracao * math.sin(math.radians(out.total_angulo))

        _assert_close_rel_percent(actual=actual_mx, expected=expected_mx, label="TRACAO.momento_x")
        _assert_close_rel_percent(actual=actual_my, expected=expected_my, label="TRACAO.momento_y")
    finally:
        wb_cqt.close()
        wb_tracao.close()
        temp_cqt.cleanup()
        temp_tracao.cleanup()
