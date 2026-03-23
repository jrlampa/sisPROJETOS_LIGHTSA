"""DTOs versionados do contrato de API para o motor de tracao."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from packages.domain.tracao.models import ResultadoTracao


class VaoDTO(BaseModel):
    """DTO de entrada para vao de tracao."""

    model_config = ConfigDict(extra="forbid")

    comprimento_m: float = Field(gt=0)
    tipo_cabo: str = Field(min_length=2, max_length=100)
    tracao_daN: float = Field(gt=0)
    azimute_graus: float = Field(ge=0, lt=360)


class PosteBrutoDTO(BaseModel):
    """DTO de entrada de poste com resistencia nominal e lista de vaos."""

    model_config = ConfigDict(extra="forbid")

    codigo: str = Field(min_length=2, max_length=50)
    resistencia_nominal_daN: float = Field(gt=0)
    vaos: list[VaoDTO] = Field(default_factory=list)


class CalcularTracaoRequest(BaseModel):
    """Payload de requisicao para calcular tracao de todos os postes do projeto."""

    model_config = ConfigDict(extra="forbid")

    postes: list[PosteBrutoDTO] = Field(min_length=1)


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
