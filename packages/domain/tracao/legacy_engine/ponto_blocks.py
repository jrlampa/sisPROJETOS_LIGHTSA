"""Ponto (1) legacy LIGHT calculation engine."""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

from .plan1_tables import (
    BTZERO_DIAM_MENSAGEIRO,
    BTZERO_DIAM_POR_FIO,
    BTZERO_PESO_MENSAGEIRO,
    BTZERO_PESO_POR_LIGACAO,
    DIAM_MENSAGEIRO,
    PESO_MENSAGEIRO,
    TIPO_ARMADO,
    TIPO_COMPACTA,
    lookup_btzero_qtd_fios,
    lookup_cable_diam,
    lookup_cable_peso,
    lookup_poste_ecc,
    lookup_rede_qtd_cabos,
)

WIND_COEFF: float = 0.00471 * 60**2  # 16.956 daN/m²


def _r(x: Any, decimals: int = 2) -> Any:
    """Excel ROUND(x, decimals) – blank/string passthrough."""
    if not isinstance(x, (int, float)):
        return x
    factor = 10**decimals
    return round(x * factor) / factor


def _roundup(x: Any, decimals: int = 0) -> Any:
    """Excel ROUNDUP(x, decimals) – always rounds away from zero."""
    if not isinstance(x, (int, float)):
        return x
    factor = 10**decimals
    if x >= 0:
        return math.ceil(x * factor) / factor
    return math.floor(x * factor) / factor


def _safe_sum(*values: Any) -> float:
    """Sum numeric values, treating blank/string as 0 (Excel SUM behaviour)."""
    return sum(v for v in values if isinstance(v, (int, float)))


def _angle_formula(sum_h: float, sum_v: float) -> float:
    if sum_h == 0:
        return _roundup(math.atan(sum_v / 1) * 180 / math.pi, 0)
    angle = math.atan(sum_v / sum_h) * 180 / math.pi
    if sum_h < 0:
        angle += 180
    return angle


def _blank(v: Any) -> str:
    """Return ' ' if v represents no active traversal."""
    return " " if not isinstance(v, (int, float)) else v


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
    tipo_rede: str = ""
    tipo_cabo: str = ""
    vao: float = 0.0
    flecha: float = 0.0
    angulo: float = 0.0
    altura_poste: float = 0.0
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


@dataclass
class TraversalCalc:
    active: bool = False
    peso_linear: Any = " "
    diam: Any = " "
    qtd_cabos: Any = " "
    peso_extra: Any = 0
    diam_extra: Any = 0
    diam_total: Any = " "
    peso_total: Any = " "
    wind_coeff: float = WIND_COEFF
    wind_H: Any = " "
    wind_V: Any = " "
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
    t = TraversalCalc()
    if not tipo_rede:
        return t

    t.active = True
    ang_rad = angulo * math.pi / 180
    t.peso_linear = lookup_cable_peso(tipo_cabo)
    t.diam = lookup_cable_diam(tipo_cabo)
    t.qtd_cabos = lookup_rede_qtd_cabos(tipo_rede)
    t.peso_extra = PESO_MENSAGEIRO if tipo_rede == TIPO_COMPACTA else 0
    t.diam_extra = DIAM_MENSAGEIRO if tipo_rede == TIPO_COMPACTA else 0
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


def _calc_bt_t1_traversal(
    mt1_t1: TraversalCalc, bt_vao: float, bt_flecha: float, bt_angulo: float
) -> TraversalCalc:
    if not mt1_t1.active:
        return TraversalCalc()
    import copy

    return copy.copy(mt1_t1)


def _calc_bt_t2_traversal(
    tipo_rede: str,
    tipo_cabo: str,
    vao: float,
    flecha: float,
    angulo: float,
) -> TraversalCalc:
    t = TraversalCalc()
    if not tipo_rede:
        return t

    t.active = True
    ang_rad = angulo * math.pi / 180

    t.peso_linear = lookup_cable_peso(tipo_cabo)
    t.diam = lookup_cable_diam(tipo_cabo)
    t.qtd_cabos = _lookup_bt_rede_qtd(tipo_rede)
    t.peso_extra = PESO_MENSAGEIRO if tipo_rede == TIPO_ARMADO else 0  # F74: Armado, not Compacta!
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
    _BT_REDE_TABLE = {
        "Multiplexada": 1,
        "Aberta": 3,
        "Armado": 1,  # workbook plan1_row=8 qtd_cabos=1 (lookup_tables.json)
    }
    return _BT_REDE_TABLE.get(tipo_rede.strip(), 0)


def _level_resultante(traversals: list[TraversalCalc]) -> float:
    sum_cat_h = _safe_sum(*(t.cat_H for t in traversals))
    sum_cat_v = _safe_sum(*(t.cat_V for t in traversals))
    sum_wind_h = _safe_sum(*(t.wind_H for t in traversals))
    sum_wind_v = _safe_sum(*(t.wind_V for t in traversals))
    return math.sqrt(sum_cat_h**2 + sum_cat_v**2) + math.sqrt(sum_wind_h**2 + sum_wind_v**2)


def _level_angle(traversals: list[TraversalCalc]) -> float:
    sum_h = _safe_sum(*(t.cat_H for t in traversals))
    sum_v = _safe_sum(*(t.cat_V for t in traversals))
    return _angle_formula(sum_h, sum_v)


def _normalize(resultante: float, altura_ancoragem: float, altura_poste: float) -> float:
    denom = altura_poste * 0.9 - 0.6 - 0.1
    if denom == 0:
        return 0.0
    return resultante * altura_ancoragem / denom


@dataclass
class LevelResult:
    resultante: float = 0.0  # raw resultante (daN) – before normalisation
    f_tip: float = 0.0  # normalised tip force (daN)
    angulo: float = 0.0  # direction (degrees)
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
    texto_total: str = ""
    texto_mt1: str = ""
    texto_mt2: str = ""
    texto_bt: str = ""
    texto_btz: str = ""
    texto_ral: str = ""


def calcular_polo(
    mt1_inputs: list[MTTraversalInput],  # 4 traversals
    mt2_inputs: list[MTTraversalInput],  # 4 traversals
    bt_inputs: list[BTTraversalInput],  # 4 traversals
    btz_inputs: list[BTZeroTraversalInput],  # 4 traversals
    ral_inputs: list[RamaisTraversalInput],  # 4 traversals
    tipo_poste: str = "",
    modelo_poste: str = "",
) -> PoloOutput:
    out = PoloOutput()
    _ensure_4(mt1_inputs, MTTraversalInput)
    _ensure_4(mt2_inputs, MTTraversalInput)
    _ensure_4(bt_inputs, BTTraversalInput)
    _ensure_4(btz_inputs, BTZeroTraversalInput)
    _ensure_4(ral_inputs, RamaisTraversalInput)

    mt1_t = [
        _calc_mt_traversal(i.tipo_rede, i.tipo_cabo, i.vao, i.flecha, i.angulo) for i in mt1_inputs
    ]
    if mt1_t[0].active:
        mt1_res = _level_resultante(mt1_t)
        mt1_ang = _level_angle(mt1_t)
        mt1_f33 = _normalize(mt1_res, mt1_inputs[0].altura_ancoragem, mt1_inputs[0].altura_poste)
    else:
        mt1_res = mt1_ang = mt1_f33 = 0.0
    out.mt1 = LevelResult(resultante=mt1_res, f_tip=mt1_f33, angulo=mt1_ang, traversals=mt1_t)

    mt2_t = [
        _calc_mt_traversal(i.tipo_rede, i.tipo_cabo, i.vao, i.flecha, i.angulo) for i in mt2_inputs
    ]
    if mt2_t[0].active:
        mt2_res = _level_resultante(mt2_t)
        mt2_ang = _level_angle(mt2_t)
        mt2_f59 = _normalize(mt2_res, mt2_inputs[0].altura_ancoragem, mt2_inputs[0].altura_poste)
    else:
        mt2_res = mt2_ang = mt2_f59 = 0.0
    out.mt2 = LevelResult(resultante=mt2_res, f_tip=mt2_f59, angulo=mt2_ang, traversals=mt2_t)

    # Alguns workbooks resolvem referencias cruzadas dentro da grade BT.
    bt_t = [
        _calc_bt_t2_traversal(
            item.tipo_rede,
            item.tipo_cabo,
            item.vao,
            item.flecha,
            item.angulo,
        )
        for item in bt_inputs
    ]

    if bt_t[0].active:
        bt_resultante = _level_resultante(bt_t)
        bt_f85 = _normalize(
            bt_resultante,
            bt_inputs[0].altura_ancoragem,
            bt_inputs[0].altura_poste,
        )
        bt_ang = _level_angle(bt_t)
    else:
        bt_resultante = bt_f85 = bt_ang = 0.0

    out.bt = LevelResult(resultante=bt_resultante, f_tip=bt_f85, angulo=bt_ang, traversals=bt_t)

    btz_t = [_calc_btzero_traversal(i) for i in btz_inputs]
    if btz_t[0].active:
        btz_res = _level_resultante(btz_t)
        btz_ang = _level_angle(btz_t)
        btz_f109 = _normalize(btz_res, btz_inputs[0].altura_ancoragem, btz_inputs[0].altura_poste)
    else:
        btz_res = btz_ang = btz_f109 = 0.0
    out.btz = LevelResult(resultante=btz_res, f_tip=btz_f109, angulo=btz_ang, traversals=btz_t)

    ral_t = [_calc_ramais_traversal(i) for i in ral_inputs]
    if ral_t[0].active:
        ral_res = _level_resultante(ral_t)
        ral_ang = _level_angle(ral_t)
        ral_f132 = _normalize(ral_res, ral_inputs[0].altura_ancoragem, ral_inputs[0].altura_poste)
    else:
        ral_res = ral_ang = ral_f132 = 0.0
    out.ral = LevelResult(resultante=ral_res, f_tip=ral_f132, angulo=ral_ang, traversals=ral_t)

    out.poste_ecc = lookup_poste_ecc(tipo_poste, modelo_poste) if tipo_poste else 0.0
    levels = [
        (mt1_f33, mt1_ang),
        (mt2_f59, mt2_ang),
        (bt_f85, bt_ang),
        (btz_f109, btz_ang if btz_t[0].active else 0.0),
        (ral_f132, ral_ang if ral_t[0].active else 0.0),
    ]
    vec_x = [f * math.cos(a * math.pi / 180) for f, a in levels]
    vec_y = [f * math.sin(a * math.pi / 180) for f, a in levels]
    sum_x = sum(vec_x)
    sum_y = sum(vec_y)

    out.total_tracao = math.sqrt(sum_x**2 + sum_y**2) + out.poste_ecc
    out.total_angulo = _angle_formula(sum_x, sum_y)

    def _txt(f: float) -> str:
        return str(int(round(f)))

    out.texto_total = f"TRAÇÃO TOTAL: {_txt(out.total_tracao)} daN {_txt(out.total_angulo)}°"
    out.texto_mt1 = (
        f"TRAÇÃO MT 1° NÍVEL (100 mm do topo): {_txt(mt1_f33)} daN {_txt(mt1_ang)}°"
        if mt1_t[0].active
        else "TRAÇÃO MT 1° NÍVEL (100 mm do topo):  daN °"
    )
    out.texto_mt2 = (
        f"TRAÇÃO MT 2° NÍVEL (100 mm do topo): {_txt(mt2_f59)} daN {_txt(mt2_ang)}°"
        if mt2_t[0].active
        else "TRAÇÃO MT 2° NÍVEL (100 mm do topo):  daN °"
    )
    out.texto_bt = (
        f"TRAÇÃO BT (100 mm do topo): {_txt(bt_f85)} daN {_txt(bt_ang)}°"
        if mt1_t[0].active
        else "TRAÇÃO BT (100 mm do topo):  daN °"
    )
    out.texto_btz = (
        f"TRAÇÃO RAMAIS BTZERO (100 mm do topo): {_txt(btz_f109)} daN {_txt(btz_ang)}°"
        if btz_t[0].active
        else "TRAÇÃO RAMAIS BTZERO (100 mm do topo):  daN °"
    )
    out.texto_ral = (
        f"TRAÇÃO RAMAIS DE LIGAÇÃO (100 mm do topo): {_txt(ral_f132)} daN {_txt(ral_ang)}°"
        if ral_t[0].active
        else "TRAÇÃO RAMAIS DE LIGAÇÃO (100 mm do topo):  daN °"
    )

    return out


def _calc_btzero_traversal(inp: BTZeroTraversalInput) -> TraversalCalc:
    t = TraversalCalc()
    if not inp.qtd_ligacoes:
        return t
    t.active = True
    ang_rad = inp.angulo * math.pi / 180

    qtd_fios = lookup_btzero_qtd_fios(inp.qtd_ligacoes)
    diam_total = qtd_fios * BTZERO_DIAM_POR_FIO + BTZERO_DIAM_MENSAGEIRO
    peso_total = inp.qtd_ligacoes * BTZERO_PESO_POR_LIGACAO + BTZERO_PESO_MENSAGEIRO

    t.diam_total = diam_total
    t.peso_total = peso_total
    t.wind_H = _r(WIND_COEFF * inp.vao / 2 * diam_total * math.cos(ang_rad))
    t.wind_V = _r(WIND_COEFF * inp.vao / 2 * diam_total * math.sin(ang_rad))
    t.catenary = (peso_total * inp.vao**2) / (8 * inp.flecha) if inp.flecha else 0.0
    t.cat_H = _r(t.catenary * math.cos(ang_rad))
    t.cat_V = _r(t.catenary * math.sin(ang_rad))
    return t


def _calc_ramais_traversal(inp: RamaisTraversalInput) -> TraversalCalc:
    t = TraversalCalc()
    if not inp.tipo_cabo or not inp.qtd_cabos:
        return t
    t.active = True
    ang_rad = inp.angulo * math.pi / 180

    t.peso_linear = lookup_cable_peso(inp.tipo_cabo)
    t.diam = lookup_cable_diam(inp.tipo_cabo)
    t.qtd_cabos = inp.qtd_cabos

    t.diam_total = inp.qtd_cabos * t.diam
    t.peso_total = t.peso_linear * inp.qtd_cabos

    t.wind_H = _r(WIND_COEFF * inp.vao / 2 * t.diam_total * math.cos(ang_rad))
    t.wind_V = _r(WIND_COEFF * inp.vao / 2 * t.diam_total * math.sin(ang_rad))
    t.catenary = (t.peso_total * inp.vao**2) / (8 * inp.flecha) if inp.flecha else 0.0
    t.cat_H = _r(t.catenary * math.cos(ang_rad))
    t.cat_V = _r(t.catenary * math.sin(ang_rad))
    return t


def _ensure_4(lst: list, cls) -> None:
    while len(lst) < 4:
        lst.append(cls())
