"""Legacy calculation engine — translated faithfully from Excel Ponto (1).

Exposes the two main public symbols:
  - calcular_polo : full catenary + wind calculation for all 5 levels
  - POSTE_TABLE   : pole eccentricity lookup table

All other symbols are available for direct import when needed.
"""

from .plan1_tables import (
    CABOS_POR_REDE,
    CABOS_TABLE,
    POSTE_TABLE,
    REDE_TABLE,
    WIND_COEFF,
    lookup_cable_diam,
    lookup_cable_peso,
    lookup_poste_ecc,
    lookup_rede_qtd_cabos,
)
from .ponto_blocks import (
    BTTraversalInput,
    BTZeroTraversalInput,
    LevelResult,
    MTTraversalInput,
    PoloOutput,
    RamaisTraversalInput,
    calcular_polo,
)

__all__ = [
    "calcular_polo",
    "MTTraversalInput",
    "BTTraversalInput",
    "BTZeroTraversalInput",
    "RamaisTraversalInput",
    "LevelResult",
    "PoloOutput",
    "CABOS_TABLE",
    "CABOS_POR_REDE",
    "POSTE_TABLE",
    "REDE_TABLE",
    "WIND_COEFF",
    "lookup_cable_diam",
    "lookup_cable_peso",
    "lookup_poste_ecc",
    "lookup_rede_qtd_cabos",
]
