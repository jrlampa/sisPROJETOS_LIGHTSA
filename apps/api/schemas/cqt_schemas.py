"""DTOs versionados do contrato de API para o motor CQT."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from apps.api.schemas.projeto_schemas import TipoProjetoDTO
from packages.domain.cqt.models import CentroCarga, CQTAnalise, TrechoEletrico


class TipoRedeDTO(str, Enum):
    """Classifica o tipo de trecho para contrato HTTP do CQT."""

    REDE = "rede"
    RAMAL = "ramal"


class CondutorDTO(BaseModel):
    """DTO de condutor para entrada e saída do CQT."""

    model_config = ConfigDict(extra="forbid")

    nome: str = Field(min_length=3, max_length=100)
    resistencia_ohm_km: float = Field(gt=0)
    ampacidade_a: float = Field(gt=0)


class TransformadorDTO(BaseModel):
    """DTO de transformador para entrada e saída do CQT."""

    model_config = ConfigDict(extra="forbid")

    id: UUID | None = None
    descricao: str = Field(min_length=3, max_length=120)
    potencia_nominal_kva: float = Field(gt=0)
    carga_maxima_lida_kva: float = Field(gt=0)
    corrente_lida_a: float | None = Field(default=None, gt=0)
    fator_carga_percent: float | None = None


class TrechoEletricoDTO(BaseModel):
    """DTO de trecho elétrico com valores de entrada e cálculos de saída."""

    model_config = ConfigDict(extra="forbid")

    id: UUID | None = None
    nome: str = Field(min_length=3, max_length=120)
    tipo_rede: TipoRedeDTO
    fases: int = Field(ge=1, le=3)
    comprimento_m: float = Field(gt=0)
    corrente_a: float = Field(gt=0)
    tensao_nominal_v: float = Field(gt=0)
    ordem_no_circuito: int = Field(default=1, ge=1)
    consumidores_montante: int | None = Field(default=None, ge=0)
    consumidores_jusante: int | None = Field(default=None, ge=0)
    fases_montante: int | None = Field(default=None, ge=1, le=3)
    fases_jusante: int | None = Field(default=None, ge=1, le=3)
    condutor: CondutorDTO
    resistencia_total_ohm: float | None = None
    queda_tensao_v: float | None = None
    queda_tensao_percent: float | None = None
    limite_qdt_percent: float | None = None
    dentro_do_limite_qdt: bool | None = None
    possui_erro_02: bool | None = None

    @classmethod
    def from_domain(cls, trecho: TrechoEletrico) -> "TrechoEletricoDTO":
        return cls.model_validate(
            {
                "id": trecho.id,
                "nome": trecho.nome,
                "tipo_rede": trecho.tipo_rede.value,
                "fases": trecho.fases,
                "comprimento_m": trecho.comprimento_m,
                "corrente_a": trecho.corrente_a,
                "tensao_nominal_v": trecho.tensao_nominal_v,
                "ordem_no_circuito": trecho.ordem_no_circuito,
                "consumidores_montante": trecho.consumidores_montante,
                "consumidores_jusante": trecho.consumidores_jusante,
                "fases_montante": trecho.fases_montante,
                "fases_jusante": trecho.fases_jusante,
                "condutor": trecho.condutor.model_dump(mode="json"),
                "resistencia_total_ohm": trecho.resistencia_total_ohm,
                "queda_tensao_v": trecho.queda_tensao_v,
                "queda_tensao_percent": trecho.queda_tensao_percent,
                "limite_qdt_percent": trecho.limite_qdt_percent,
                "dentro_do_limite_qdt": trecho.dentro_do_limite_qdt,
                "possui_erro_02": trecho.possui_erro_02,
            }
        )


class CentroCargaDTO(BaseModel):
    """DTO de centro de carga com trafo e trechos da análise."""

    model_config = ConfigDict(extra="forbid")

    id: UUID | None = None
    nome: str = Field(min_length=3, max_length=120)
    transformador: TransformadorDTO
    trechos: list[TrechoEletricoDTO] = Field(min_length=1)
    queda_total_percent: float | None = None
    possui_erro_02: bool | None = None

    @classmethod
    def from_domain(cls, centro: CentroCarga) -> "CentroCargaDTO":
        return cls.model_validate(
            {
                "id": centro.id,
                "nome": centro.nome,
                "transformador": {
                    **centro.transformador.model_dump(mode="json"),
                    "fator_carga_percent": centro.transformador.fator_carga_percent,
                },
                "trechos": [
                    TrechoEletricoDTO.from_domain(item).model_dump(mode="json")
                    for item in centro.trechos
                ],
                "queda_total_percent": centro.queda_total_percent,
                "possui_erro_02": centro.possui_erro_02,
            }
        )


class CQTAnaliseRequest(BaseModel):
    """Payload de requisição para execução da análise CQT."""

    model_config = ConfigDict(extra="forbid")

    tipo_projeto: TipoProjetoDTO
    centro_carga: CentroCargaDTO
    recuperacao_clandestino_confirmada: bool | None = None
    quantidade_ligacoes_irregulares: int | None = Field(default=None, ge=1)
    recebeu_leitura_trafo_maxima: bool = False
    corrente_trafo_a: float | None = Field(default=None, gt=0)
    carga_maxima_transformador_kva: float | None = Field(default=None, gt=0)


class CQTAnaliseResponse(BaseModel):
    """Resposta da análise CQT com cálculos já consolidados."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    tipo_projeto: TipoProjetoDTO
    centro_carga: CentroCargaDTO
    limite_carregamento_trafo_percent: float
    trafo_dentro_do_limite: bool
    qdt_total_dentro_do_limite: bool
    criado_em: datetime

    @classmethod
    def from_domain(cls, analise: CQTAnalise) -> "CQTAnaliseResponse":
        return cls.model_validate(
            {
                "id": analise.id,
                "tipo_projeto": analise.tipo_projeto.value,
                "centro_carga": CentroCargaDTO.from_domain(analise.centro_carga).model_dump(
                    mode="json"
                ),
                "limite_carregamento_trafo_percent": analise.limite_carregamento_trafo_percent,
                "trafo_dentro_do_limite": analise.trafo_dentro_do_limite,
                "qdt_total_dentro_do_limite": analise.qdt_total_dentro_do_limite,
                "criado_em": analise.criado_em,
            }
        )
