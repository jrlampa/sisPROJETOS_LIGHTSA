"""Entidades e regras puras do motor de tracao mecanica poste a poste."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from math import cos, radians, sin, sqrt
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, computed_field


def utc_now() -> datetime:
    """Padroniza timestamps em UTC para rastreabilidade do resultado."""
    return datetime.now(timezone.utc)


class EstadoMecanico(str, Enum):
    """Classificacao do carregamento mecanico de um poste.

    Limiares aplicados sobre o percentual de carregamento em relacao
    a resistencia nominal do poste:
    - APROVADO:  carregamento <= 80%
    - ALERTA:    80% < carregamento <= 105%
    - REPROVADO: carregamento > 105%
    """

    APROVADO = "APROVADO"
    ALERTA = "ALERTA"
    REPROVADO = "REPROVADO"


class Vao(BaseModel):
    """Trecho de rede entre dois postes com tracao horizontal aplicada.

    O azimute representa a direcao em que o cabo tensiona o poste,
    usando convencao geografica (0=Norte, 90=Leste, 180=Sul, 270=Oeste).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID = Field(default_factory=uuid4)
    comprimento_m: float = Field(gt=0)
    tipo_cabo: str = Field(min_length=2, max_length=100)
    tracao_daN: float = Field(gt=0, description="Tensao horizontal do cabo em daN.")
    azimute_graus: float = Field(
        ge=0, lt=360, description="Direcao do vao a partir do poste (0=N, 90=E, 180=S, 270=O)."
    )


class Poste(BaseModel):
    """Estrutura de suporte com calculo vetorial dos esforcos mecanicos.

    O esforco resultante e calculado como somatorio vetorial das tracoes
    de todos os vaos conectados. Para poste de passagem com vaos simetricos,
    as tracoes opostas se anulam. Para poste de fim de linha, a resultante
    e igual a tracao do unico vao.

    Formula (convencao bussola):
        Fx = sum(T_i * sin(azimute_i_rad))
        Fy = sum(T_i * cos(azimute_i_rad))
        Resultante = sqrt(Fx^2 + Fy^2)
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID = Field(default_factory=uuid4)
    codigo: str = Field(min_length=2, max_length=50)
    resistencia_nominal_daN: float = Field(
        gt=0, description="Resistencia mecanica nominal do poste em daN."
    )
    vaos: tuple[Vao, ...] = Field(default_factory=tuple)

    @computed_field
    @property
    def esforco_resultante_daN(self) -> float:
        """Resultante vetorial horizontal de todos os vaos conectados."""
        fx = sum(v.tracao_daN * sin(radians(v.azimute_graus)) for v in self.vaos)
        fy = sum(v.tracao_daN * cos(radians(v.azimute_graus)) for v in self.vaos)
        return sqrt(fx**2 + fy**2)

    @computed_field
    @property
    def percentual_carregamento(self) -> float:
        """Percentual de carregamento em relacao a resistencia nominal."""
        return (self.esforco_resultante_daN / self.resistencia_nominal_daN) * 100

    @computed_field
    @property
    def estado_mecanico(self) -> EstadoMecanico:
        """Classificacao tecnica do poste baseada no percentual de carregamento."""
        p = self.percentual_carregamento
        if p > 105.0:
            return EstadoMecanico.REPROVADO
        if p > 80.0:
            return EstadoMecanico.ALERTA
        return EstadoMecanico.APROVADO


class ResultadoTracao(BaseModel):
    """Registro imutavel do calculo mecanico para um poste em um momento especifico.

    Captura os valores calculados na instante da analise para garantir
    rastreabilidade historica independente de alteracoes futuras no Poste.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID = Field(default_factory=uuid4)
    poste: Poste
    esforco_resultante_daN: float
    percentual_carregamento: float
    estado_mecanico: EstadoMecanico
    calculado_em: datetime

    @classmethod
    def calcular(cls, poste: Poste) -> "ResultadoTracao":
        """Instancia o resultado a partir das propriedades calculadas do poste."""
        return cls(
            poste=poste,
            esforco_resultante_daN=poste.esforco_resultante_daN,
            percentual_carregamento=poste.percentual_carregamento,
            estado_mecanico=poste.estado_mecanico,
            calculado_em=utc_now(),
        )
