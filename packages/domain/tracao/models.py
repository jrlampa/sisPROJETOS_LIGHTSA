"""Entidades e regras puras do motor de tracao mecanica poste a poste.

O esforco_resultante_daN pode ser calculado por dois caminhos:

  1. Motor Fisico (preferencial): forneca ``traversals_fisicas`` ao Poste.
     Cada TraversalFisica carrega os dados fisicos completos de uma travessia
     (vao, flecha, angulo, tipo_rede, tipo_cabo, alturas) e o calculo e
     delegado ao ``legacy_engine.calcular_polo`` — motor fiel ao workbook
     Excel com caternaria, vento e arredondamentos intermediarios identicos
     ao ROUND() do Excel.

  2. Soma Vetorial Simples (retrocompativel): forneca apenas ``vaos`` com
     ``tracao_daN`` e ``azimute_graus`` pre-calculados.  Util para testes
     unitarios de logica de classificacao (APROVADO / ALERTA / REPROVADO)
     sem depender dos dados fisicos de cabo.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from math import cos, radians, sin, sqrt
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator


def utc_now() -> datetime:
    """Padroniza timestamps em UTC para rastreabilidade do resultado."""
    return datetime.now(timezone.utc)


# ---------------------------------------------------------------------------
# Motor fisico — dados de entrada para calcular_polo do legacy_engine
# ---------------------------------------------------------------------------


class NivelTracao(str, Enum):
    """Identificador do nivel eletrico de uma travessia no poste."""

    MT1 = "MT1"
    MT2 = "MT2"
    BT = "BT"
    BTZ = "BTZ"
    RAL = "RAL"


class TraversalFisica(BaseModel):
    """Dados fisicos de uma travessia (uma posicao 1-4 em um nivel).

    Mapeia diretamente para MTTraversalInput / BTTraversalInput /
    BTZeroTraversalInput / RamaisTraversalInput do legacy_engine.

    Para o nivel BT:
      - T1 (posicao=1): apenas ``altura_ancoragem_m`` e informalmente
        ``tipo_rede``/``tipo_cabo`` sao usados; a geometria vao/flecha/angulo
        e ``altura_poste_m`` sao herdados de MT1 T1 (regra C66=C14 do Excel).
      - T2 (posicao=2): ``tipo_rede``/``tipo_cabo`` proprios; geometria
        herdada de MT1 T2 (F66=F14).
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    nivel: NivelTracao
    posicao: int = Field(ge=1, le=4, default=1)
    tipo_rede: str = ""
    tipo_cabo: str = ""
    vao_m: float = Field(ge=0, default=0.0, description="Comprimento do vao em metros.")
    flecha_m: float = Field(ge=0, default=0.0, description="Flecha do cabo em metros.")
    angulo_graus: float = Field(
        ge=0, lt=360, default=0.0, description="Angulo de deflexao em graus."
    )
    altura_poste_m: float = Field(ge=0, default=0.0)
    altura_ancoragem_m: float = Field(ge=0, default=0.0)
    qtd_ligacoes: float = Field(
        ge=0, default=0.0, description="Quantidade de ligacoes (apenas BTZ)."
    )
    qtd_cabos: float = Field(ge=0, default=0.0, description="Quantidade de cabos (apenas RAL).")

    @model_validator(mode="after")
    def _flecha_required_when_vao(self) -> "TraversalFisica":
        if self.vao_m > 0 and self.flecha_m <= 0:
            raise ValueError("flecha_m deve ser > 0 quando vao_m > 0")
        return self


# ---------------------------------------------------------------------------
# Helper: delega ao legacy_engine com agrupamento por nivel/posicao
# ---------------------------------------------------------------------------


def _calcular_via_motor_legado(
    traversals: tuple[TraversalFisica, ...],
    tipo_poste: str,
    modelo_poste: str,
) -> float:
    """Chama calcular_polo do legacy_engine e retorna total_tracao (daN).

    Agrupa as TraversalFisica por nivel (MT1/MT2/BT/BTZ/RAL) e posicao (1-4),
    preenche os slots vazios com instancias inativas, e delega ao motor
    legado que reproduz fielmente as 289 formulas do workbook Excel.
    """
    from .legacy_engine.ponto_blocks import (  # lazy import — sem circular deps
        BTTraversalInput,
        BTZeroTraversalInput,
        MTTraversalInput,
        RamaisTraversalInput,
        calcular_polo,
    )

    # Indexar por (nivel, posicao) para lookup O(1)
    idx: dict[tuple[str, int], TraversalFisica] = {
        (t.nivel.value, t.posicao): t for t in traversals
    }

    def _get(nivel: str, pos: int) -> TraversalFisica | None:
        return idx.get((nivel, pos))

    def _mt_inputs(nivel: str) -> list[MTTraversalInput]:
        result = []
        for pos in range(1, 5):
            t = _get(nivel, pos)
            if t:
                result.append(
                    MTTraversalInput(
                        tipo_rede=t.tipo_rede,
                        tipo_cabo=t.tipo_cabo,
                        vao=t.vao_m,
                        flecha=t.flecha_m,
                        angulo=t.angulo_graus,
                        altura_poste=t.altura_poste_m,
                        altura_ancoragem=t.altura_ancoragem_m,
                    )
                )
            else:
                result.append(MTTraversalInput())
        return result

    # BT inputs
    bt_list: list[BTTraversalInput] = []
    for pos in range(1, 5):
        t = _get("BT", pos)
        if t:
            bt_list.append(
                BTTraversalInput(
                    tipo_rede=t.tipo_rede,
                    tipo_cabo=t.tipo_cabo,
                    vao=t.vao_m,
                    flecha=t.flecha_m,
                    angulo=t.angulo_graus,
                    altura_poste=t.altura_poste_m,
                    altura_ancoragem=t.altura_ancoragem_m,
                )
            )
        else:
            bt_list.append(BTTraversalInput())

    # BTZ inputs
    btz_list: list[BTZeroTraversalInput] = []
    for pos in range(1, 5):
        t = _get("BTZ", pos)
        if t:
            btz_list.append(
                BTZeroTraversalInput(
                    qtd_ligacoes=t.qtd_ligacoes,
                    vao=t.vao_m,
                    flecha=t.flecha_m,
                    angulo=t.angulo_graus,
                    altura_poste=t.altura_poste_m,
                    altura_ancoragem=t.altura_ancoragem_m,
                )
            )
        else:
            btz_list.append(BTZeroTraversalInput())

    # RAL inputs
    ral_list: list[RamaisTraversalInput] = []
    for pos in range(1, 5):
        t = _get("RAL", pos)
        if t:
            ral_list.append(
                RamaisTraversalInput(
                    tipo_cabo=t.tipo_cabo,
                    qtd_cabos=t.qtd_cabos,
                    vao=t.vao_m,
                    flecha=t.flecha_m,
                    angulo=t.angulo_graus,
                    altura_poste=t.altura_poste_m,
                    altura_ancoragem=t.altura_ancoragem_m,
                )
            )
        else:
            ral_list.append(RamaisTraversalInput())

    output = calcular_polo(
        mt1_inputs=_mt_inputs("MT1"),
        mt2_inputs=_mt_inputs("MT2"),
        bt_inputs=bt_list,
        btz_inputs=btz_list,
        ral_inputs=ral_list,
        tipo_poste=tipo_poste,
        modelo_poste=modelo_poste,
    )
    return output.total_tracao


# ---------------------------------------------------------------------------
# EstadoMecanico
# ---------------------------------------------------------------------------


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
    """Estrutura de suporte com calculo dos esforcos mecanicos.

    Suporta dois modos de calculo:

    **Motor Fisico** (preferencial — paridade 100% com Excel):
        Preencha ``traversals_fisicas`` com os dados fisicos de cada travessia
        (vao, flecha, angulo, tipo_rede, tipo_cabo, alturas) e opcionalmente
        ``tipo_poste``/``modelo_poste`` para incluir a excentricidade do poste.
        O ``esforco_resultante_daN`` sera calculado pelo legacy_engine usando
        a formula exata: catenaria parabólica + pressao de vento + composicao
        vetorial com ROUND() intermediarios identicos ao workbook.

    **Soma Vetorial Simples** (retrocompativel):
        Preencha apenas ``vaos`` com ``tracao_daN`` e ``azimute_graus``
        pre-calculados. Formula bussola (0=Norte, 90=Leste):
            Fx = sum(T_i * sin(az_i))
            Fy = sum(T_i * cos(az_i))
            Resultante = sqrt(Fx^2 + Fy^2)
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID = Field(default_factory=uuid4)
    codigo: str = Field(min_length=2, max_length=50)
    resistencia_nominal_daN: float = Field(
        gt=0, description="Resistencia mecanica nominal do poste em daN."
    )
    # Modo simples: tracoes e azimutes pre-calculados
    vaos: tuple[Vao, ...] = Field(default_factory=tuple)
    # Modo fisico: dados completos para o motor legado
    traversals_fisicas: tuple[TraversalFisica, ...] = Field(
        default_factory=tuple,
        description="Traversals fisicas para calcular_polo do legacy_engine.",
    )
    tipo_poste: str = Field(
        default="",
        description="Tipo do poste para lookup de excentricidade (ECC).",
    )
    modelo_poste: str = Field(
        default="",
        description="Modelo do poste para lookup de excentricidade (ECC).",
    )

    @computed_field
    @property
    def esforco_resultante_daN(self) -> float:
        """Resultante dos esforcos mecanicos horizontais aplicados ao poste.

        Usa o motor fisico (legacy_engine.calcular_polo) quando
        ``traversals_fisicas`` esta preenchido; caso contrario, efetua a
        soma vetorial simples sobre ``vaos``.
        """
        if self.traversals_fisicas:
            return _calcular_via_motor_legado(
                self.traversals_fisicas, self.tipo_poste, self.modelo_poste
            )
        # Fallback: soma vetorial simples (convencao bussola)
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
