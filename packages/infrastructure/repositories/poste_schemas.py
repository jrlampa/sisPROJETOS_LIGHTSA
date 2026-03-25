"""Schemas Pydantic para as rotas de Postes."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel

from packages.application.query_models import PosteConsolidado


class TrechoConectadoResponse(BaseModel):
    id: UUID
    nome: str
    tipo_conexao: str
    condutor_nome: str
    comprimento_m: float


class ResultadoTracaoResumoResponse(BaseModel):
    esforco_resultante_daN: float
    percentual_carregamento: float
    estado_mecanico: str


class PosteConsolidadoResponse(BaseModel):
    id: UUID
    codigo: str
    resistencia_nominal_daN: float | None
    resultado_tracao: ResultadoTracaoResumoResponse | None
    trechos_conectados: list[TrechoConectadoResponse]

    @classmethod
    def from_domain(cls, domain_model: PosteConsolidado) -> "PosteConsolidadoResponse":
        return cls.model_validate(domain_model.model_dump())