"""Entidades e regras puras do motor de CQT."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, computed_field


def utc_now() -> datetime:
    """Padroniza timestamps em UTC para rastreabilidade do resultado."""
    return datetime.now(timezone.utc)


class TipoProjetoCQT(str, Enum):
    """Tipos de projeto que podem gerar uma analise CQT."""

    RECON = "RECON"
    CLANDESTINO = "CLANDESTINO"


class TipoRede(str, Enum):
    """Tipos de rede eletrica de baixa tensao."""

    CONVENCIONAL = "CONVENCIONAL"
    ISOLADA = "ISOLADA"
    MULTIPLEXADA = "MULTIPLEXADA"


class Condutor(BaseModel):
    """Propriedades eletricas de um condutor."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    nome: str
    resistencia_ohm_km: float
    ampacidade_a: float


class TrechoEletrico(BaseModel):
    """Segmento de circuito entre dois postes, com suas propriedades eletricas."""

    model_config = ConfigDict(extra="forbid", frozen=True, populate_by_name=True)

    id: UUID = Field(default_factory=uuid4)
    poste_de_codigo: str = Field(min_length=1, max_length=50)
    poste_para_codigo: str = Field(min_length=1, max_length=50)
    condutor: Condutor
    tipo_rede: TipoRede
    fases: int = Field(default=3, ge=1, le=3)
    comprimento_m: float = Field(gt=0)
    corrente_a: float = Field(ge=0)
    tensao_nominal_v: float = Field(default=220.0, gt=0)
    ordem_no_circuito: int = Field(ge=1)
    consumidores_montante: int | None = Field(default=None, ge=0)
    consumidores_jusante: int | None = Field(default=None, ge=0)
    fases_montante: int | None = Field(default=None, ge=1, le=3)
    fases_jusante: int | None = Field(default=None, ge=1, le=3)

    @computed_field
    @property
    def nome(self) -> str:
        """Nome do trecho, derivado dos postes de início e fim."""
        return f"{self.poste_de_codigo}-{self.poste_para_codigo}"

    @computed_field
    @property
    def resistencia_total_ohm(self) -> float:
        """Resistencia total do trecho, considerando o comprimento."""
        return (self.condutor.resistencia_ohm_km / 1000) * self.comprimento_m

    @computed_field
    @property
    def queda_tensao_v(self) -> float:
        """Queda de tensao (em Volts) no trecho."""
        return self.resistencia_total_ohm * self.corrente_a

    @computed_field
    @property
    def queda_tensao_percent(self) -> float:
        """Queda de tensao (em percentual) no trecho."""
        if self.tensao_nominal_v == 0:
            return 0.0
        return (self.queda_tensao_v / self.tensao_nominal_v) * 100

    @property
    def limite_qdt_percent(self) -> float:
        """Limite regulatorio de queda de tensao para o tipo de rede."""
        return 5.0 if self.tipo_rede is TipoRede.CONVENCIONAL else 7.0

    @computed_field
    @property
    def dentro_do_limite_qdt(self) -> bool:
        """Indica se o trecho esta dentro do limite de queda de tensao."""
        return self.queda_tensao_percent <= self.limite_qdt_percent

    @computed_field
    @property
    def possui_erro_02(self) -> bool:
        """Placeholder para a regra de negocio 'ERRO 02'."""
        return False


class Transformador(BaseModel):
    """Transformador que alimenta o centro de carga."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    id: UUID = Field(default_factory=uuid4)
    descricao: str
    potencia_nominal_kva: float
    carga_maxima_lida_kva: float = 0.0
    corrente_lida_a: float | None = None

    @computed_field
    @property
    def fator_carga_percent(self) -> float:
        """Percentual de carregamento do transformador."""
        if self.potencia_nominal_kva == 0:
            return 0.0
        return (self.carga_maxima_lida_kva / self.potencia_nominal_kva) * 100


class CentroCarga(BaseModel):
    """Agregador de trechos eletricos alimentados por um mesmo transformador."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    id: UUID = Field(default_factory=uuid4)
    nome: str
    transformador: Transformador
    trechos: tuple[TrechoEletrico, ...]

    @computed_field
    @property
    def queda_total_percent(self) -> float:
        """Queda de tensao acumulada do transformador ate o ultimo consumidor."""
        return sum(t.queda_tensao_percent for t in self.trechos)

    @computed_field
    @property
    def possui_erro_02(self) -> bool:
        """Indica se algum trecho do centro de carga possui 'ERRO 02'."""
        return any(t.possui_erro_02 for t in self.trechos)


class CQTAnalise(BaseModel):
    """Entidade raiz que representa uma analise CQT completa."""

    model_config = ConfigDict(extra="forbid", frozen=True)
    id: UUID = Field(default_factory=uuid4)
    tipo_projeto: TipoProjetoCQT
    centro_carga: CentroCarga
    recuperacao_clandestino_confirmada: bool | None = None
    quantidade_ligacoes_irregulares: int | None = None
    recebeu_leitura_trafo_maxima: bool = False
    corrente_trafo_a: float | None = None
    carga_maxima_transformador_kva: float | None = None
    limite_carregamento_trafo_percent: float = 80.0
    criado_em: datetime = Field(default_factory=utc_now)

    @computed_field
    @property
    def trafo_dentro_do_limite(self) -> bool:
        """Indica se o transformador esta operando dentro do limite de carga."""
        return (
            self.centro_carga.transformador.fator_carga_percent
            <= self.limite_carregamento_trafo_percent
        )

    @computed_field
    @property
    def qdt_total_dentro_do_limite(self) -> bool:
        """Indica se a queda de tensao total do circuito esta dentro do limite."""
        return all(t.dentro_do_limite_qdt for t in self.centro_carga.trechos)