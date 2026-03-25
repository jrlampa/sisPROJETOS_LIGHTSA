"""Entidades e regras puras para calculo de CQT (queda de tensao)."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from math import sqrt
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator

from packages.domain.intake.models import TipoProjeto


def utc_now() -> datetime:
    """Padroniza timestamps em UTC para rastreabilidade da analise."""

    return datetime.now(timezone.utc)


class TipoRede(str, Enum):
    """Classifica o tipo de trecho para aplicacao de limite de QDT."""

    REDE = "rede"
    RAMAL = "ramal"


class Condutor(BaseModel):
    """Representa os parametros eletricos basicos do condutor.

    A resistencia por km e usada no calculo de queda de tensao do trecho.
    A ampacidade define o teto de corrente admissivel no trecho.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    nome: str = Field(min_length=3, max_length=100)
    resistencia_ohm_km: float = Field(gt=0)
    ampacidade_a: float = Field(gt=0)


class Transformador(BaseModel):
    """Representa o transformador principal associado a analise CQT."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID = Field(default_factory=uuid4)
    descricao: str = Field(min_length=3, max_length=120)
    potencia_nominal_kva: float = Field(gt=0)
    carga_maxima_lida_kva: float = Field(gt=0)
    corrente_lida_a: float | None = Field(default=None, gt=0)

    @computed_field
    @property
    def fator_carga_percent(self) -> float:
        """Retorna o carregamento percentual do transformador."""

        return (self.carga_maxima_lida_kva / self.potencia_nominal_kva) * 100


class TrechoEletrico(BaseModel):
    """Trecho elementar do circuito para calculo de queda de tensao.

    Formula aplicada:
    - Trifasico: ΔV = sqrt(3) * I * R_total
    - Monofasico: ΔV = I * R_total
    onde R_total = resistencia_ohm_km * comprimento_km.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID = Field(default_factory=uuid4)
    nome: str = Field(min_length=3, max_length=120)
    tipo_rede: TipoRede = TipoRede.REDE
    fases: int = Field(default=3)
    comprimento_m: float = Field(gt=0)
    corrente_a: float = Field(gt=0)
    tensao_nominal_v: float = Field(gt=0)
    condutor: Condutor
    ordem_no_circuito: int = Field(default=1, ge=1)
    consumidores_montante: int | None = Field(default=None, ge=0)
    consumidores_jusante: int | None = Field(default=None, ge=0)
    fases_montante: int | None = Field(default=None, ge=1, le=3)
    fases_jusante: int | None = Field(default=None, ge=1, le=3)
    # TODO (Legacy Quirks): quando presente, usa a queda percentual do workbook
    # para reproduzir exatamente o legado Excel em cenarios de paridade.
    queda_tensao_percent_legacy: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validar_parametros(self) -> "TrechoEletrico":
        if self.fases not in (1, 3):
            raise ValueError("Trecho eletrico aceita apenas configuracao monofasica ou trifasica.")
        if self.corrente_a > self.condutor.ampacidade_a:
            raise ValueError("Corrente do trecho excede a ampacidade do condutor selecionado.")
        return self

    @computed_field
    @property
    def resistencia_total_ohm(self) -> float:
        """Resistencia equivalente do trecho em ohms."""

        return self.condutor.resistencia_ohm_km * (self.comprimento_m / 1000)

    @computed_field
    @property
    def queda_tensao_v(self) -> float:
        """Queda de tensao absoluta no trecho em volts."""

        if self.queda_tensao_percent_legacy is not None:
            return (self.queda_tensao_percent_legacy / 100) * self.tensao_nominal_v

        if self.fases == 3:
            return sqrt(3) * self.corrente_a * self.resistencia_total_ohm
        return self.corrente_a * self.resistencia_total_ohm

    @computed_field
    @property
    def queda_tensao_percent(self) -> float:
        """Queda percentual de tensao do trecho."""

        if self.queda_tensao_percent_legacy is not None:
            return self.queda_tensao_percent_legacy

        return (self.queda_tensao_v / self.tensao_nominal_v) * 100

    @computed_field
    @property
    def limite_qdt_percent(self) -> float:
        """Limite de QDT aplicado ao trecho conforme tipo de rede."""

        return 1.5 if self.tipo_rede is TipoRede.RAMAL else 5.0

    @computed_field
    @property
    def dentro_do_limite_qdt(self) -> bool:
        """Indica se o trecho atende o limite de QDT aplicavel."""

        return self.queda_tensao_percent <= self.limite_qdt_percent

    @computed_field
    @property
    def possui_erro_02(self) -> bool:
        """Detecta a inconsistencia logica conhecida como Erro 02.

        Regra: em um fluxo valido, fases e consumidores nao devem aumentar a jusante.
        """

        if self.consumidores_montante is not None and self.consumidores_jusante is not None and self.consumidores_jusante > self.consumidores_montante:
            return True
        if self.fases_montante is not None and self.fases_jusante is not None and self.fases_jusante > self.fases_montante:
            return True
        return False


class CentroCarga(BaseModel):
    """Consolida os trechos eletricos e o transformador da analise CQT."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID = Field(default_factory=uuid4)
    nome: str = Field(min_length=3, max_length=120)
    transformador: Transformador
    # TODO (Legacy Quirks): o workbook Excel agrega a queda do MT + transformador
    # ao acumulado de BT. Mantemos esta parcela explicita para paridade 1:1.
    queda_base_percent: float = Field(default=0, ge=0)
    trechos: tuple[TrechoEletrico, ...] = Field(min_length=1)

    @computed_field
    @property
    def queda_total_percent(self) -> float:
        """Soma da queda percentual de tensao em todos os trechos da analise."""

        return self.queda_base_percent + sum(trecho.queda_tensao_percent for trecho in self.trechos)

    @computed_field
    @property
    def possui_erro_02(self) -> bool:
        """Sinaliza se algum trecho apresenta inconsistencia a jusante."""

        return any(trecho.possui_erro_02 for trecho in self.trechos)


class CQTAnalise(BaseModel):
    """Entidade agregadora do motor CQT com regras de negocio LIGHT.

    Regras aplicadas:
    - Projeto normal: limite de carregamento do trafo em 85%.
    - Recuperacao de clandestino: limite mais conservador, 80%.
    - Clandestino exige confirmacao de recuperacao e quantidade de ligacoes.
    - Projeto nao clandestino exige leitura de trafo quando a flag for ativa.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID = Field(default_factory=uuid4)
    tipo_projeto: TipoProjeto
    centro_carga: CentroCarga
    recuperacao_clandestino_confirmada: bool | None = None
    quantidade_ligacoes_irregulares: int | None = Field(default=None, ge=1)
    recebeu_leitura_trafo_maxima: bool = False
    corrente_trafo_a: float | None = Field(default=None, gt=0)
    carga_maxima_transformador_kva: float | None = Field(default=None, gt=0)
    criado_em: datetime = Field(default_factory=utc_now)

    @computed_field
    @property
    def limite_carregamento_trafo_percent(self) -> float:
        """Retorna o limite de carregamento aplicavel ao contexto da analise."""

        if self.tipo_projeto is TipoProjeto.CLANDESTINOS:
            return 80.0
        return 85.0

    @computed_field
    @property
    def trafo_dentro_do_limite(self) -> bool:
        """Indica conformidade do transformador no cenário analisado."""

        return (
            self.centro_carga.transformador.fator_carga_percent
            <= self.limite_carregamento_trafo_percent
        )

    @computed_field
    @property
    def qdt_total_dentro_do_limite(self) -> bool:
        """Indica se todos os trechos respeitam o limite de QDT."""

        return all(trecho.dentro_do_limite_qdt for trecho in self.centro_carga.trechos)

    def _validar_consistencia_geral(self) -> None:
        """Valida regras de negocio aplicaveis a todos os tipos de projeto."""
        if self.centro_carga.possui_erro_02:
            raise ValueError("Erro 02 detectado: fases ou consumidores aumentaram a jusante.")

        if not self.trafo_dentro_do_limite:
            raise ValueError(
                "Carregamento do transformador excede o limite permitido para o tipo de projeto."
            )

    def _validar_regras_clandestino(self) -> None:
        """Valida regras especificas para projetos de recuperacao de clandestinos."""
        if self.recuperacao_clandestino_confirmada is not True:
            raise ValueError(
                "Projeto de clandestinos exige confirmacao de recuperacao de clandestino."
            )
        if self.quantidade_ligacoes_irregulares is None:
            raise ValueError("Projeto de clandestinos exige quantidade de ligacoes irregulares.")
        if self.recebeu_leitura_trafo_maxima or self.corrente_trafo_a is not None:
            raise ValueError("Projeto de clandestinos nao deve depender de leitura maxima de trafo.")
        if self.carga_maxima_transformador_kva is not None:
            raise ValueError(
                "Projeto de clandestinos nao deve receber carga maxima informada manualmente na analise CQT."
            )

    def _validar_regras_projeto_normal(self) -> None:
        """Valida regras para projetos que nao sao de recuperacao de clandestinos."""
        if self.recuperacao_clandestino_confirmada is not None:
            raise ValueError("Campos de clandestino nao podem ser usados em projetos normais.")
        if self.quantidade_ligacoes_irregulares is not None:
            raise ValueError(
                "Quantidade de ligacoes irregulares so pode ser informada em clandestinos."
            )
        if self.recebeu_leitura_trafo_maxima:
            if self.corrente_trafo_a is None or self.carga_maxima_transformador_kva is None:
                raise ValueError(
                    "Leitura maxima do trafo exige corrente e carga maxima informadas na analise."
                )

    @model_validator(mode="after")
    def validar_regras_por_contexto(self) -> "CQTAnalise":
        self._validar_consistencia_geral()

        if self.tipo_projeto is TipoProjeto.CLANDESTINOS:
            self._validar_regras_clandestino()
        else:
            self._validar_regras_projeto_normal()

        return self
