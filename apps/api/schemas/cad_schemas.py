"""DTOs versionados do contrato de API para o motor CAD 2.5D.

O sumário de importacao expoe apenas contagens agregadas para evitar a
transferencia de milhares de coordenadas pela rede.
"""

from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from packages.domain.cad.models import ArquivoDXF


class LayerSumarioDTO(BaseModel):
    """Sumário de uma layer técnica importada — nome e contagem de segmentos."""

    model_config = ConfigDict(extra="forbid")

    nome: str
    cor_autocad: int
    total_segmentos: int
    comprimento_total_xy: float = Field(ge=0)


class ImportacaoDxfResponse(BaseModel):
    """DTO de resposta ao upload de um ficheiro DXF.

    Expõe apenas metadados e agregados para não trafegar coordenadas brutas.
    """

    model_config = ConfigDict(extra="forbid")

    arquivo_id: UUID
    nome_arquivo: str
    versao_dxf: str
    total_layers: int = Field(ge=0)
    total_segmentos: int = Field(ge=0)
    layers: list[LayerSumarioDTO]
    importado_em: datetime

    @classmethod
    def from_domain(cls, arquivo: ArquivoDXF) -> "ImportacaoDxfResponse":
        """Constrói o DTO de sumário a partir da entidade de domínio ArquivoDXF."""
        layers = [
            LayerSumarioDTO(
                nome=geom.layer_tecnica.nome,
                cor_autocad=geom.layer_tecnica.cor_autocad,
                total_segmentos=len(geom.segmentos),
                comprimento_total_xy=geom.comprimento_total_xy,
            )
            for geom in arquivo.geometrias
        ]
        return cls(
            arquivo_id=arquivo.id,
            nome_arquivo=arquivo.nome_arquivo,
            versao_dxf=arquivo.versao,
            total_layers=len(arquivo.geometrias),
            total_segmentos=arquivo.quantidade_segmentos,
            layers=layers,
            importado_em=arquivo.criado_em,
        )
