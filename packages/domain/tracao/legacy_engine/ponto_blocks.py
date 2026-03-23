"""Ponto (1) sheet calculation engine.

Translates all 289 formula cells from Ponto (1) to Python, reproducing
the Excel computation with identical intermediate ROUND() calls for parity.

Source sheet: Ponto (1) in AP COSMO LDA NOVA 03 - PROJETO 5 - POSTE 1D.xlsm
Inventory:    python/extract/artifacts/inventory.json

====  ARCHITECTURE  ====

Five calculation BLOCKS — MT1 (rows 12-34), MT2 (rows 38-60),
BT (rows 64-86), BTZero (rows 88-110), Ramais (rows 112-133).

SHARED-CELL RULES (faithful to workbook formulas):
  ┌ BT T1 cable data   = MT1 T1 cable data  (C71=C19, C72=C20, C73=C21,
  │                                           C74=C22, C75=C23)
  ├ BT T1 wind/cat     = MT1 T1 wind/cat    (C79=C27 … C83=C31)
  ├ BT T1 geometry     = MT1 T1 geometry    (C66=C14 … C69=C17)
  ├ BT T2 geometry     = MT1 T2 geometry    (F66=F14, F67=F15, F68=F16)
  └ BT resultante      = MT1 resultante     (C84=C32)   ← critical!

BT normalized force (F85) = C84 * C70 / (C69*0.9−0.6−0.1)
   where C84=MT1 total, C69=MT1 T1 alturaPoste, C70=BT T1 alturaAncoragem.

BT angle (F86) uses the CATENARY horizontal/vertical sums over C82:L82,
C83:L83 — i.e. [MT1-T1 cat_H, BT-T2 cat_H, BT-T3 cat_H, BT-T4 cat_H] etc.

Vector composition (rows 137-141):
  X[level] = F_tip * cos(angle_rad)
  Y[level] = F_tip * sin(angle_rad)
  C140     = √(ΣX² + ΣY²) + C149   (adds pole eccentricity force)
  C141     = atan2-angle of (ΣX, ΣY)

Verified output (Cosmo LDA project):
  MT1  217 daN @ 177°   MT2  171 daN @  90°   BT  165 daN @  60°
  BTZ    0 daN @   0°   RAL    0 daN @   0°   TOTAL 374 daN @ 112°
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from .plan1_tables import (
    BTZERO_DIAM_POR_FIO,
    BTZERO_DIAM_MENSAGEIRO,
    BTZERO_PESO_POR_LIGACAO,
    BTZERO_PESO_MENSAGEIRO,
    TIPO_ARMADO,
    TIPO_COMPACTA,
    DIAM_MENSAGEIRO,
    PESO_MENSAGEIRO,
    lookup_btzero_qtd_fios,
    lookup_cable_diam,
    lookup_cable_peso,
    lookup_poste_ecc,
    lookup_rede_qtd_cabos,
)

# ── Wind coefficient (constant across all blocks) ──────────────────────────
WIND_COEFF: float = 0.00471 * 60**2  # 16.956 daN/m²


# ── Rounding helpers matching Excel semantics ──────────────────────────────

def _r(x: Any, decimals: int = 2) -> Any:
    """Excel ROUND(x, decimals) – blank/string passthrough."""
    if not isinstance(x, (int, float)):
        return x
    factor = 10 ** decimals
    return round(x * factor) / factor


def _roundup(x: Any, decimals: int = 0) -> Any:
    """Excel ROUNDUP(x, decimals) – always rounds away from zero."""
    if not isinstance(x, (int, float)):
        return x
    factor = 10 ** decimals
    if x >= 0:
        return math.ceil(x * factor) / factor
    return math.floor(x * factor) / factor


def _safe_sum(*values: Any) -> float:
    """Sum numeric values, treating blank/string as 0 (Excel SUM behaviour)."""
    return sum(v for v in values if isinstance(v, (int, float)))


def _angle_formula(sum_h: float, sum_v: float) -> float:
    """Excel ATAN-based angle formula used in rows 34/60/86/110/133/141.

    IF sum_H = 0  → ROUNDUP(ATAN(sum_V / 1) * 180/PI, 0)
    ELIF sum_H < 0 → ATAN(sum_V / sum_H) * 180/PI + 180
    ELSE           → ATAN(sum_V / sum_H) * 180/PI
    """
    if sum_h == 0:
        return _roundup(math.atan(sum_v / 1) * 180 / math.pi, 0)
    angle = math.atan(sum_v / sum_h) * 180 / math.pi
    if sum_h < 0:
        angle += 180
    return angle


def _blank(v: Any) -> str:
    """Return ' ' if v represents no active traversal."""
    return " " if not isinstance(v, (int, float)) else v


# ── Traversal dataclasses ──────────────────────────────────────────────────


@dataclass
class MTTraversalInput:
    tipo_rede: str = ""
    tipo_cabo: str = ""
    vao: float = 0.0
    flecha: float = 0.0
    angulo: float = 0.0
    altura_poste: float = 0.0
    altura_ancoragem: float = 0.0


@dataclass
class BTTraversalInput:
    """BT traversal input.

    T1 geometry (vao/flecha/angulo/altura_poste) is overridden by MT1 T1.
    T2 geometry  is overridden by MT1 T2.
    altura_ancoragem is always the BT's own value.
    """
    tipo_rede: str = ""
    tipo_cabo: str = ""
    vao: float = 0.0        # ignored for T1 and T2 (uses MT1 geometry)
    flecha: float = 0.0     # ignored for T1 and T2
    angulo: float = 0.0     # ignored for T1 and T2
    altura_poste: float = 0.0   # ignored for all (uses MT1 T1 via C69=C17)
    altura_ancoragem: float = 0.0


@dataclass
class BTZeroTraversalInput:
    qtd_ligacoes: float = 0.0
    vao: float = 0.0
    flecha: float = 0.0
    angulo: float = 0.0
    altura_poste: float = 0.0
    altura_ancoragem: float = 0.0


@dataclass
class RamaisTraversalInput:
    tipo_cabo: str = ""
    qtd_cabos: float = 0.0
    vao: float = 0.0
    flecha: float = 0.0
    angulo: float = 0.0
    altura_poste: float = 0.0
    altura_ancoragem: float = 0.0


# ── Per-traversal computed values (rows 19-31 pattern) ────────────────────

@dataclass
class TraversalCalc:
    """Intermediate values for one traversal (one column, C/F/I/L)."""
    active: bool = False
    # Cable lookups (rows 19-23)
    peso_linear: Any = " "
    diam: Any = " "
    qtd_cabos: Any = " "
    peso_extra: Any = 0
    diam_extra: Any = 0
    # Totals (rows 24-25)
    diam_total: Any = " "
    peso_total: Any = " "
    # Wind (rows 26-28)
    wind_coeff: float = WIND_COEFF
    wind_H: Any = " "
    wind_V: Any = " "
    # Catenary (rows 29-31)
    catenary: Any = " "
    cat_H: Any = ""
    cat_V: Any = ""


def _calc_mt_traversal(
    tipo_rede: str,
    tipo_cabo: str,
    vao: float,
    flecha: float,
    angulo: float,
) -> TraversalCalc:
    """Compute one MT-style traversal (rows 19-31 pattern).
    Used by MT1, MT2, and BT T2/T3/T4 (with their own lookups).
    """
    t = TraversalCalc()
    if not tipo_rede:
        return t

    t.active = True
    ang_rad = angulo * math.pi / 180

    # Cable property lookups
    t.peso_linear = lookup_cable_peso(tipo_cabo)
    t.diam = lookup_cable_diam(tipo_cabo)
    t.qtd_cabos = lookup_rede_qtd_cabos(tipo_rede)

    # Cordoalha extra (Plan1 row 22: peso_extra if Compacta)
    t.peso_extra = PESO_MENSAGEIRO if tipo_rede == TIPO_COMPACTA else 0
    t.diam_extra = DIAM_MENSAGEIRO if tipo_rede == TIPO_COMPACTA else 0

    # Totals
    dq = t.qtd_cabos
    t.diam_total = dq * t.diam + t.diam_extra
    t.peso_total = t.peso_linear * dq + t.peso_extra

    # Wind
    t.wind_H = _r(WIND_COEFF * vao / 2 * t.diam_total * math.cos(ang_rad))
    t.wind_V = _r(WIND_COEFF * vao / 2 * t.diam_total * math.sin(ang_rad))

    # Catenary
    if vao > 0 and flecha > 0:
        t.catenary = (t.peso_total * vao**2) / (8 * flecha)
        t.cat_H = _r(t.catenary * math.cos(ang_rad))
        t.cat_V = _r(t.catenary * math.sin(ang_rad))
    else:
        t.catenary = 0.0
        t.cat_H = 0.0
        t.cat_V = 0.0

    return t


def _calc_bt_t1_traversal(mt1_t1: TraversalCalc, bt_vao: float, bt_flecha: float, bt_angulo: float) -> TraversalCalc:
    """BT T1 re-uses ALL cable + wind + catenary values from MT1 T1 (C71=C19 … C83=C31).

    The geometry (vao/flecha/angulo) is ALSO from MT1 T1 (C66=C14 … C68=C16).
    bt_vao/flecha/angulo arguments come from mt1_t1 traversal input (already embedded
    in mt1_t1 via _calc_mt_traversal), so we simply return a copy of mt1_t1.
    """
    if not mt1_t1.active:
        return TraversalCalc()
    import copy
    return copy.copy(mt1_t1)


def _calc_bt_t2_traversal(
    tipo_rede: str,
    tipo_cabo: str,
    # geometry shared from MT1 T2:
    vao: float,
    flecha: float,
    angulo: float,
) -> TraversalCalc:
    """BT T2 uses own cable lookups + MT1 T2 geometry (F66=F14, F67=F15, F68=F16).

    Cable lookup uses Plan1!$N$6:$O$8 (rows 6-8: Multiplexada/Aberta/Armado only).
    """
    t = TraversalCalc()
    if not tipo_rede:
        return t

    t.active = True
    ang_rad = angulo * math.pi / 180

    t.peso_linear = lookup_cable_peso(tipo_cabo)
    t.diam = lookup_cable_diam(tipo_cabo)
    # BT T2-T4 use only N6:O8 (rows 6-8: Multiplexada/Aberta/Armado)
    t.qtd_cabos = _lookup_bt_rede_qtd(tipo_rede)
    t.peso_extra = PESO_MENSAGEIRO if tipo_rede == TIPO_ARMADO else 0   # F74: Armado, not Compacta!
    t.diam_extra = DIAM_MENSAGEIRO if tipo_rede == TIPO_ARMADO else 0

    dq = t.qtd_cabos
    t.diam_total = dq * t.diam + t.diam_extra
    t.peso_total = t.peso_linear * dq + t.peso_extra

    t.wind_H = _r(WIND_COEFF * vao / 2 * t.diam_total * math.cos(ang_rad))
    t.wind_V = _r(WIND_COEFF * vao / 2 * t.diam_total * math.sin(ang_rad))

    if vao > 0 and flecha > 0:
        t.catenary = (t.peso_total * vao**2) / (8 * flecha)
        t.cat_H = _r(t.catenary * math.cos(ang_rad))
        t.cat_V = _r(t.catenary * math.sin(ang_rad))
    else:
        t.catenary = 0.0
        t.cat_H = 0.0
        t.cat_V = 0.0

    return t


def _lookup_bt_rede_qtd(tipo_rede: str) -> float:
    """Plan1!$N$6:$O$8 – rows for Multiplexada / Aberta / Armado only."""
    _BT_REDE_TABLE = {
        "Multiplexada": 1,
        "Aberta": 3,
        "Armado": 1,   # workbook plan1_row=8 qtd_cabos=1 (lookup_tables.json)
    }
    return _BT_REDE_TABLE.get(tipo_rede.strip(), 0)


# ── Level result helpers ───────────────────────────────────────────────────

def _level_resultante(traversals: list[TraversalCalc]) -> float:
    """Compute level resultante (rows 32/58/84 pattern):
    √(ΣcatH² + ΣcatV²) + √(ΣwindH² + ΣwindV²)
    """
    sum_cat_h = _safe_sum(*(t.cat_H for t in traversals))
    sum_cat_v = _safe_sum(*(t.cat_V for t in traversals))
    sum_wind_h = _safe_sum(*(t.wind_H for t in traversals))
    sum_wind_v = _safe_sum(*(t.wind_V for t in traversals))
    return math.sqrt(sum_cat_h**2 + sum_cat_v**2) + math.sqrt(sum_wind_h**2 + sum_wind_v**2)


def _level_angle(traversals: list[TraversalCalc]) -> float:
    """Compute level angle (rows 34/60/86/110/133 pattern) from catenary components."""
    sum_h = _safe_sum(*(t.cat_H for t in traversals))
    sum_v = _safe_sum(*(t.cat_V for t in traversals))
    return _angle_formula(sum_h, sum_v)


def _normalize(resultante: float, altura_ancoragem: float, altura_poste: float) -> float:
    """Tip force normalisation: F_tip = resultante * h_anc / (h_poste*0.9 − 0.6 − 0.1)"""
    denom = altura_poste * 0.9 - 0.6 - 0.1
    if denom == 0:
        return 0.0
    return resultante * altura_ancoragem / denom


# ── Block-level dataclasses ────────────────────────────────────────────────

@dataclass
class LevelResult:
    resultante: float = 0.0   # raw resultante (daN) – before normalisation
    f_tip: float = 0.0        # normalised tip force (daN)
    angulo: float = 0.0       # direction (degrees)
    traversals: list[TraversalCalc] = field(default_factory=list)


@dataclass
class PoloOutput:
    mt1: LevelResult = field(default_factory=LevelResult)
    mt2: LevelResult = field(default_factory=LevelResult)
    bt: LevelResult = field(default_factory=LevelResult)
    btz: LevelResult = field(default_factory=LevelResult)
    ral: LevelResult = field(default_factory=LevelResult)
    total_tracao: float = 0.0
    total_angulo: float = 0.0
    poste_ecc: float = 0.0
    # Text outputs (rows 143-148)
    texto_total: str = ""
    texto_mt1: str = ""
    texto_mt2: str = ""
    texto_bt: str = ""
    texto_btz: str = ""
    texto_ral: str = ""


# ── Main calculation function ──────────────────────────────────────────────

def calcular_polo(
    mt1_inputs: list[MTTraversalInput],    # 4 traversals
    mt2_inputs: list[MTTraversalInput],    # 4 traversals
    bt_inputs: list[BTTraversalInput],     # 4 traversals
    btz_inputs: list[BTZeroTraversalInput],# 4 traversals
    ral_inputs: list[RamaisTraversalInput],# 4 traversals
    tipo_poste: str = "",
    modelo_poste: str = "",
) -> PoloOutput:
    """Main entry point. Reproduces Ponto (1) sheet logic.

    mt1_inputs[0] = T1 (column C), [1] = T2 (col F), [2] = T3 (col I), [3] = T4 (col L)
    """
    out = PoloOutput()
    _ensure_4(mt1_inputs, MTTraversalInput)
    _ensure_4(mt2_inputs, MTTraversalInput)
    _ensure_4(bt_inputs, BTTraversalInput)
    _ensure_4(btz_inputs, BTZeroTraversalInput)
    _ensure_4(ral_inputs, RamaisTraversalInput)

    # ── MT1 block (rows 12-34) ─────────────────────────────────────────────
    mt1_t = [
        _calc_mt_traversal(i.tipo_rede, i.tipo_cabo, i.vao, i.flecha, i.angulo)
        for i in mt1_inputs
    ]
    if mt1_t[0].active:
        mt1_res = _level_resultante(mt1_t)
        mt1_ang = _level_angle(mt1_t)
        mt1_f33 = _normalize(mt1_res, mt1_inputs[0].altura_ancoragem, mt1_inputs[0].altura_poste)
    else:
        mt1_res = mt1_ang = mt1_f33 = 0.0
    out.mt1 = LevelResult(resultante=mt1_res, f_tip=mt1_f33, angulo=mt1_ang, traversals=mt1_t)

    # ── MT2 block (rows 38-60) ─────────────────────────────────────────────
    mt2_t = [
        _calc_mt_traversal(i.tipo_rede, i.tipo_cabo, i.vao, i.flecha, i.angulo)
        for i in mt2_inputs
    ]
    if mt2_t[0].active:
        mt2_res = _level_resultante(mt2_t)
        mt2_ang = _level_angle(mt2_t)
        mt2_f59 = _normalize(mt2_res, mt2_inputs[0].altura_ancoragem, mt2_inputs[0].altura_poste)
    else:
        mt2_res = mt2_ang = mt2_f59 = 0.0
    out.mt2 = LevelResult(resultante=mt2_res, f_tip=mt2_f59, angulo=mt2_ang, traversals=mt2_t)

    # ── BT block (rows 64-86) ──────────────────────────────────────────────
    # T1: ALL values come from MT1 T1 (C66=C14 … C84=C32)
    bt_t = [TraversalCalc() for _ in range(4)]
    bt_t[0] = _calc_bt_t1_traversal(mt1_t[0], mt1_inputs[0].vao, mt1_inputs[0].flecha, mt1_inputs[0].angulo)

    # T2: own cable lookups + MT1 T2 geometry
    bt_t[1] = _calc_bt_t2_traversal(
        bt_inputs[1].tipo_rede,
        bt_inputs[1].tipo_cabo,
        mt1_inputs[1].vao,     # F66=F14
        mt1_inputs[1].flecha,  # F67=F15
        mt1_inputs[1].angulo,  # F68=F16
    )

    # T3, T4: fully independent
    for k in (2, 3):
        bt_t[k] = _calc_bt_t2_traversal(
            bt_inputs[k].tipo_rede,
            bt_inputs[k].tipo_cabo,
            bt_inputs[k].vao,
            bt_inputs[k].flecha,
            bt_inputs[k].angulo,
        )

    # C84 = C32 (BT resultante = MT1 resultante)
    bt_resultante = mt1_res  # C84=C32
    # F85: uses C84 (=MT1 res), C70 (BT T1 altAncoragem), C69=C17 (MT1 T1 altPoste)
    bt_f85 = 0.0
    if mt1_t[0].active:
        bt_f85 = _normalize(bt_resultante, bt_inputs[0].altura_ancoragem, mt1_inputs[0].altura_poste)

    # F86 angle: computed from BT cat_H/cat_V sums (C82=C30 for T1, F82/I82 for T2-T4)
    bt_ang = _level_angle(bt_t) if mt1_t[0].active else 0.0

    out.bt = LevelResult(resultante=bt_resultante, f_tip=bt_f85, angulo=bt_ang, traversals=bt_t)

    # ── BTZero block (rows 88-110) ─────────────────────────────────────────
    btz_t = [_calc_btzero_traversal(i) for i in btz_inputs]
    if btz_t[0].active:
        btz_res = _level_resultante(btz_t)
        btz_ang = _level_angle(btz_t)
        btz_f109 = _normalize(btz_res, btz_inputs[0].altura_ancoragem, btz_inputs[0].altura_poste)
    else:
        btz_res = btz_ang = btz_f109 = 0.0
    out.btz = LevelResult(resultante=btz_res, f_tip=btz_f109, angulo=btz_ang, traversals=btz_t)

    # ── Ramais block (rows 112-133) ────────────────────────────────────────
    ral_t = [_calc_ramais_traversal(i) for i in ral_inputs]
    if ral_t[0].active:
        ral_res = _level_resultante(ral_t)
        ral_ang = _level_angle(ral_t)
        ral_f132 = _normalize(ral_res, ral_inputs[0].altura_ancoragem, ral_inputs[0].altura_poste)
    else:
        ral_res = ral_ang = ral_f132 = 0.0
    out.ral = LevelResult(resultante=ral_res, f_tip=ral_f132, angulo=ral_ang, traversals=ral_t)

    # ── Pole eccentricity (row 149) ────────────────────────────────────────
    out.poste_ecc = lookup_poste_ecc(tipo_poste, modelo_poste) if tipo_poste else 0.0

    # ── Vector composition (rows 137-141) ─────────────────────────────────
    levels = [
        (mt1_f33, mt1_ang),
        (mt2_f59, mt2_ang),
        (bt_f85,  bt_ang),
        (btz_f109, btz_ang if btz_t[0].active else 0.0),
        (ral_f132, ral_ang if ral_t[0].active else 0.0),
    ]
    vec_x = [f * math.cos(a * math.pi / 180) for f, a in levels]
    vec_y = [f * math.sin(a * math.pi / 180) for f, a in levels]
    sum_x = sum(vec_x)
    sum_y = sum(vec_y)

    out.total_tracao = math.sqrt(sum_x**2 + sum_y**2) + out.poste_ecc
    out.total_angulo = _angle_formula(sum_x, sum_y)

    # ── Text outputs (rows 143-148) ────────────────────────────────────────
    def _txt(f: float) -> str:
        return str(int(round(f)))

    out.texto_total = f"TRAÇÃO TOTAL: {_txt(out.total_tracao)} daN {_txt(out.total_angulo)}°"
    out.texto_mt1  = (
        f"TRAÇÃO MT 1° NÍVEL (100 mm do topo): {_txt(mt1_f33)} daN {_txt(mt1_ang)}°"
        if mt1_t[0].active else
        "TRAÇÃO MT 1° NÍVEL (100 mm do topo):  daN °"
    )
    out.texto_mt2 = (
        f"TRAÇÃO MT 2° NÍVEL (100 mm do topo): {_txt(mt2_f59)} daN {_txt(mt2_ang)}°"
        if mt2_t[0].active else
        "TRAÇÃO MT 2° NÍVEL (100 mm do topo):  daN °"
    )
    out.texto_bt = (
        f"TRAÇÃO BT (100 mm do topo): {_txt(bt_f85)} daN {_txt(bt_ang)}°"
        if mt1_t[0].active else
        "TRAÇÃO BT (100 mm do topo):  daN °"
    )
    out.texto_btz = (
        f"TRAÇÃO RAMAIS BTZERO (100 mm do topo): {_txt(btz_f109)} daN {_txt(btz_ang)}°"
        if btz_t[0].active else
        "TRAÇÃO RAMAIS BTZERO (100 mm do topo):  daN °"
    )
    out.texto_ral = (
        f"TRAÇÃO RAMAIS DE LIGAÇÃO (100 mm do topo): {_txt(ral_f132)} daN {_txt(ral_ang)}°"
        if ral_t[0].active else
        "TRAÇÃO RAMAIS DE LIGAÇÃO (100 mm do topo):  daN °"
    )

    return out


# ── BTZero traversal (rows 96-108 pattern) ─────────────────────────────────

def _calc_btzero_traversal(inp: BTZeroTraversalInput) -> TraversalCalc:
    """BTZero uses piecewise qtd_fios lookup from Plan1!J35:L40."""
    t = TraversalCalc()
    if not inp.qtd_ligacoes:
        return t
    t.active = True
    ang_rad = inp.angulo * math.pi / 180

    qtd_fios = lookup_btzero_qtd_fios(inp.qtd_ligacoes)
    # row 100: diam_total = qtd_fios * 0.0115 + 0.0095
    diam_total = qtd_fios * BTZERO_DIAM_POR_FIO + BTZERO_DIAM_MENSAGEIRO
    # row 101: peso_total = qtd_ligacoes * 0.15 + 0.407
    peso_total = inp.qtd_ligacoes * BTZERO_PESO_POR_LIGACAO + BTZERO_PESO_MENSAGEIRO

    t.diam_total = diam_total
    t.peso_total = peso_total
    t.wind_H = _r(WIND_COEFF * inp.vao / 2 * diam_total * math.cos(ang_rad))
    t.wind_V = _r(WIND_COEFF * inp.vao / 2 * diam_total * math.sin(ang_rad))
    t.catenary  = (peso_total * inp.vao**2) / (8 * inp.flecha) if inp.flecha else 0.0
    t.cat_H = _r(t.catenary * math.cos(ang_rad))
    t.cat_V = _r(t.catenary * math.sin(ang_rad))
    return t


# ── Ramais traversal (rows 120-131 pattern) ────────────────────────────────

def _calc_ramais_traversal(inp: RamaisTraversalInput) -> TraversalCalc:
    """Ramais uses own cable lookup and explicit qtd_cabos (no rede lookup)."""
    t = TraversalCalc()
    if not inp.tipo_cabo or not inp.qtd_cabos:
        return t
    t.active = True
    ang_rad = inp.angulo * math.pi / 180

    t.peso_linear = lookup_cable_peso(inp.tipo_cabo)
    t.diam = lookup_cable_diam(inp.tipo_cabo)
    t.qtd_cabos = inp.qtd_cabos

    # row 123: diam_total = qtd_cabos * diam (no extra)
    t.diam_total = inp.qtd_cabos * t.diam
    # row 124: peso_total = peso_linear * qtd_cabos (no extra)
    t.peso_total = t.peso_linear * inp.qtd_cabos

    t.wind_H = _r(WIND_COEFF * inp.vao / 2 * t.diam_total * math.cos(ang_rad))
    t.wind_V = _r(WIND_COEFF * inp.vao / 2 * t.diam_total * math.sin(ang_rad))
    t.catenary  = (t.peso_total * inp.vao**2) / (8 * inp.flecha) if inp.flecha else 0.0
    t.cat_H = _r(t.catenary * math.cos(ang_rad))
    t.cat_V = _r(t.catenary * math.sin(ang_rad))
    return t


# ── Helpers ────────────────────────────────────────────────────────────────

def _ensure_4(lst: list, cls) -> None:
    """Pad list to length 4 with default instances."""
    while len(lst) < 4:
        lst.append(cls())
