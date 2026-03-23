"""Static lookup tables translated from Plan1 of the workbook."""
from __future__ import annotations


def _vlookup(key: str, table: list, col_index: int):
    key_norm = str(key).strip().lower()
    for row in table:
        if str(row[0]).strip().lower() == key_norm:
            return row[col_index - 1]
    return None

WIND_COEFF: float = 0.00471 * 60 ** 2

CABOS_TABLE: list[list] = [
    ["556MCM-CA, Nu",              0.022,    0.779],
    ["397MCM-CA, Nu",              0.0184,   0.558],
    ["1/0AWG-CAA, Nu",             0.0102,   0.217],
    ["4 AWG-CAA, Nu",              0.0064,   0.085],
    ["397MCM-CA, XLPE, 34,5 kV",   0.034,    1.195],
    ["397MCM-CA, XLPE, 13,8 kV",   0.026,    0.749],
    ["1/0AWG-CAA, XLPE, 13,8 kV",  0.017,    0.370],
    ["4 AWG-CAA, XLPE, 13,8 kV",   0.0132,   0.193],
    ["185mm\u00b2, MTX-MT, 20/35 kV",   0.100,    5.370],
    ["185mm\u00b2, MTX-MT, 12/20 kV",   0.088,    4.430],
    ["50mm\u00b2, MTX-MT, 12/20 kV",    0.067,    2.480],
    ["397MCM-CA, PVC",             0.024,    0.660],
    ["1/0AWG-CAA, PVC ",           0.0132,   0.192],
    ["240mm\u00b2, MTX-BT ",            0.061,    2.745],
    ["185mm\u00b2, MTX-BT ",            0.058,    2.334],
    ["70mm\u00b2, MTX-BT ",             0.030,    1.008],
    ["Cabo armado 240mm\u00b2 ",        0.065,    5.250],
    ["Cabo armado 95mm\u00b2 ",         0.043,    2.300],
    ["Cordoalha de aco 3/8\" ",    0.0095,   0.407],
    ["10 mm\u00b2 - Bipolar",           0.00970,  0.097],
    ["10 mm\u00b2 - Tetrapolar",        0.0176,   0.313],
    ["16 mm\u00b2 - Bipolar",           0.0115,   0.136],
    ["16 mm\u00b2 - Tetrapolar",        0.0218,   0.459],
    ["6-AWG, MTX-BT  - Duplex",    0.01209,  0.113],
    ["6-AWG, MTX-BT  - Triplex",   0.01410,  0.173],
    ["6-AWG, MTX-BT  - Quadriplex",0.017484, 0.232],
    ["4-AWG, MTX-BT",              0.020936, 0.349],
    ["1/0-AWG, MTX-BT ",           0.0255,   0.834],
    ["Cabo armado 25mm\u00b2 ",         0.0285,   1.080],
    ["Cabo armado 50mm\u00b2 ",         0.0345,   1.450],
    ["4/0-AWG, MTX-BT ",           0.0347,   1.560],
    ["3/0-AWG, MTX-BT ",           0.0313,   1.270],
    ["4-AWG, MTX-BT ",             0.01630,  0.349],
]

REDE_TABLE: list[list] = [
    ["Compacta",     3],
    ["Convencional", 3],
    ["Multiplexado", 1],
    ["Multiplexada", 1],
    ["Aberta ",      3],
    ["Armado",       1],
]

TIPO_COMPACTA: str = "Compacta"
TIPO_ARMADO: str   = "Armado"

PESO_MENSAGEIRO: float = 0.407
DIAM_MENSAGEIRO: float = 0.0095

BTZERO_PESO_POR_LIGACAO: float = 0.15
BTZERO_DIAM_POR_FIO: float     = 0.0115
BTZERO_PESO_MENSAGEIRO: float  = 0.407
BTZERO_DIAM_MENSAGEIRO: float  = 0.0095

POSTE_TABLE: dict[str, list[list]] = {
    "Concreto circular": [
        ["9 m / 150 daN",  12.24],
        ["9 m / 300 daN",  14.18],
        ["11 m / 300 daN", 18.49],
        ["11 m / 600 daN", 20.09],
        ["11 m / 1000 daN",23.27],
        ["11 m / 1500 daN",28.06],
        ["12 m / 300 daN", 20.78],
        ["12 m / 600 daN", 22.53],
        ["12 m / 1000 daN",26.02],
        ["12 m / 2000 daN",34.76],
        ["15 m / 1000 daN",34.83],
        ["18 m / 1000 daN",44.46],
    ],
    "Fibra de vidro circular": [
        ["9 m / 300 daN",  12.21],
        ["11 m / 300 daN", 18.51],
        ["11 m / 600 daN", 19.66],
        ["12 m / 600 daN", 22.09],
    ],
    "Concreto Duplo T": [
        ["9 m / 300 daN",  21.55],
        ["11 m / 300 daN", 28.78],
        ["11 m / 600 daN", 28.78],
        ["12 m / 600 daN", 32.58],
    ],
    "Metalico": [
        ["7,5 m / 200 daN", 7.51],
    ],
}
POSTE_TABLE["Concreto duplo T"] = POSTE_TABLE["Concreto Duplo T"]


def lookup_cable_diam(tipo_cabo: str):
    return _vlookup(tipo_cabo, CABOS_TABLE, col_index=2)


def lookup_cable_peso(tipo_cabo: str):
    return _vlookup(tipo_cabo, CABOS_TABLE, col_index=3)


def lookup_rede_qtd_cabos(tipo_rede: str):
    return _vlookup(tipo_rede, REDE_TABLE, col_index=2)


def lookup_btzero_qtd_fios(qtd_ligacoes: float) -> int:
    breakpoints = [3, 8, 20, 38, 61]
    qtd_fios    = [1, 3,  5,  7,  9, 11]
    for i, bp in enumerate(breakpoints):
        if qtd_ligacoes < bp:
            return qtd_fios[i]
    return qtd_fios[-1]


def lookup_poste_ecc(tipo_poste: str, modelo_poste: str) -> float:
    for key, rows in POSTE_TABLE.items():
        if key.strip().lower() == tipo_poste.strip().lower():
            result = _vlookup(modelo_poste, rows, col_index=2)
            if result is not None:
                return float(result)
    return 0.0
# Source of truth: plan4_selectors.py (extracted from Plan4 of workbook)
CABOS_POR_REDE = {
    # MT redes — Plan4 A1:C12
    "Compacta": [
        "397MCM-CA, XLPE, 34,5 kV",
        "397MCM-CA, XLPE, 13,8 kV",
        "1/0AWG-CAA, XLPE, 13,8 kV",
        "4 AWG-CAA, XLPE, 13,8 kV",
        "185mm², MTX-MT, 20/35 kV",
        "185mm², MTX-MT, 12/20 kV",
        "50mm², MTX-MT, 12/20 kV",
    ],
    "Convencional": [
        "556MCM-CA, Nu",
        "397MCM-CA, Nu",
        "1/0AWG-CAA, Nu",
        "4 AWG-CAA, Nu",
        "397MCM-CA, XLPE, 34,5 kV",
        "397MCM-CA, XLPE, 13,8 kV",
        "1/0AWG-CAA, XLPE, 13,8 kV",
        "4 AWG-CAA, XLPE, 13,8 kV",
    ],
    "Multiplexado": [
        "185mm², MTX-MT, 20/35 kV",
        "185mm², MTX-MT, 12/20 kV",
        "50mm², MTX-MT, 12/20 kV",
    ],
    # BT redes — Plan4 A13:C16
    "Multiplexada": [
        "240mm², MTX-BT ",
        "185mm², MTX-BT ",
        "70mm², MTX-BT ",
    ],
    "Aberta ": [
        "397MCM-CA, PVC",
        "1/0AWG-CAA, PVC ",
    ],
    "Armado": [
        "Cabo armado 240mm² ",
        "Cabo armado 95mm² ",
    ],
}
