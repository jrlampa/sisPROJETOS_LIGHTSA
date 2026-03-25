"""Modelos de leitura (read models) para casos de uso de consulta."""

from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field


class TrechoConectado(BaseModel):
    """Representa um trecho elétrico conectado a um poste."""

    id: UUID
    nome: str
    tipo_conexao: str = Field(description="'de' (saída) ou 'para' (chegada)")
    condutor_nome: str
    comprimento_m: float


class ResultadoTracaoResumo(BaseModel):
    """Resumo do resultado da análise de tração para um poste."""

    esforco_resultante_daN: float
    percentual_carregamento: float
    estado_mecanico: str


class PosteConsolidado(BaseModel):
    """Modelo de leitura que agrega todas as informações de um poste."""

    id: UUID
    codigo: str
    resistencia_nominal_daN: float | None
    resultado_tracao: ResultadoTracaoResumo | None
    trechos_conectados: list[TrechoConectado]