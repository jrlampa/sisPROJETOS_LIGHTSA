"""DTOs versionados do contrato de API para o motor de tracao."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from packages.application.dtos.tracao import (
    CalcularTracaoRequestDTO,
    PosteBrutoDTO,
    VaoDTO,
)
from packages.domain.tracao.models import ResultadoTracao

CalcularTracaoRequest = CalcularTracaoRequestDTO


class ResultadoTracaoDTO(BaseModel):
    """DTO de saida com os indicadores mecanicos calculados por poste."""

    model_config = ConfigDict(extra="forbid")

    esforco_resultante_daN: float
    percentual_carregamento: float
    estado_mecanico: str

    @classmethod
    def from_domain(cls, resultado: ResultadoTracao) -> "ResultadoTracaoDTO":
        return cls.model_validate(
            {
                "esforco_resultante_daN": resultado.esforco_resultante_daN,
                "percentual_carregamento": resultado.percentual_carregamento,
                "estado_mecanico": resultado.estado_mecanico.value,
            }
        )


class CalcularTracaoResponse(BaseModel):
    """Resposta da API com todos os resultados de tracao calculados."""

    model_config = ConfigDict(extra="forbid")

    resultados: list[ResultadoTracaoDTO]


__all__ = [
    "VaoDTO",
    "PosteBrutoDTO",
    "CalcularTracaoRequest",
    "ResultadoTracaoDTO",
    "CalcularTracaoResponse",
]
