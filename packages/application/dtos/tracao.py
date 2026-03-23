"""DTOs Pydantic V2 para entrada de dados do motor de tracao."""

from __future__ import annotations

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

SafeText = Annotated[str, StringConstraints(strip_whitespace=True, pattern=r"^[^<>]*$")]


class VaoDTO(BaseModel):
    """DTO de entrada para vao de tracao com coercao segura de numeros."""

    model_config = ConfigDict(extra="forbid")

    comprimento_m: float = Field(gt=0)
    tipo_cabo: SafeText = Field(min_length=2, max_length=100)
    tracao_daN: float = Field(gt=0)
    azimute_graus: float = Field(ge=0, lt=360)

    @field_validator("comprimento_m", "tracao_daN", mode="before")
    @classmethod
    def validar_float_positivo(cls, value: object) -> float:
        if isinstance(value, str):
            normalized = value.strip().replace(",", ".")
        else:
            normalized = value

        try:
            parsed = float(normalized)
        except (TypeError, ValueError) as exc:
            raise ValueError("valor numerico invalido") from exc

        if parsed <= 0:
            raise ValueError("valor deve ser maior que zero")

        return parsed


class PosteBrutoDTO(BaseModel):
    """DTO de entrada de poste com resistencia nominal e lista de vaos."""

    model_config = ConfigDict(extra="forbid")

    codigo: SafeText = Field(min_length=2, max_length=50)
    resistencia_nominal_daN: float = Field(gt=0)
    vaos: list[VaoDTO] = Field(default_factory=list)

    @field_validator("resistencia_nominal_daN", mode="before")
    @classmethod
    def validar_resistencia_positiva(cls, value: object) -> float:
        if isinstance(value, str):
            normalized = value.strip().replace(",", ".")
        else:
            normalized = value

        try:
            parsed = float(normalized)
        except (TypeError, ValueError) as exc:
            raise ValueError("resistencia nominal invalida") from exc

        if parsed <= 0:
            raise ValueError("resistencia nominal deve ser maior que zero")

        return parsed


class CalcularTracaoRequestDTO(BaseModel):
    """Payload de requisicao para calcular tracao de todos os postes do projeto."""

    model_config = ConfigDict(extra="forbid")

    postes: list[PosteBrutoDTO] = Field(min_length=1)
