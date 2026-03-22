"""Entidades do levantamento inicial e das evidencias do projeto."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from packages.domain.workflow.models import EtapaProjeto


def utc_now() -> datetime:
    """Retorna data e hora em UTC para padronizar eventos de dominio."""

    return datetime.now(timezone.utc)


class TipoProjeto(str, Enum):
    """Lista controlada dos tipos de projeto aceitos na triagem."""

    LIGACAO_NOVA = "Ligacao Nova"
    ROBUSTEZ_MT = "Robustez MT"
    ROBUSTEZ_BT = "Robustez BT"
    CLANDESTINOS = "Clandestinos"
    RECONDUTORAMENTO = "Recondutoramento"
    EXTENSAO_REDE = "Extensao de Rede"
    SUBDIVISAO_CIRCUITO = "Subdivisao de Circuito"


class TipoEvidencia(str, Enum):
    """Classifica a origem da evidencia usada na analise tecnica."""

    FOTO_CAMPO = "Foto de Campo"
    STREET_VIEW = "Street View"
    DESENHO_REFERENCIA = "Desenho de Referencia"
    LEVANTAMENTO = "Levantamento"
    DOCUMENTO = "Documento"
    OUTRO = "Outro"


class Evidencia(BaseModel):
    """Representa um artefato consultado para validar o levantamento de campo.

    A regra de negocio exige que toda evidencia tenha descricao e pelo menos
    uma origem identificavel, seja por caminho local ou URL.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID = Field(default_factory=uuid4)
    tipo: TipoEvidencia
    descricao: str = Field(min_length=3, max_length=500)
    caminho_arquivo: str | None = Field(default=None, min_length=3, max_length=500)
    url: HttpUrl | None = None
    coletado_em: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validar_origem(self) -> "Evidencia":
        if not self.caminho_arquivo and self.url is None:
            raise ValueError(
                "A evidencia deve informar um caminho de arquivo ou uma URL de origem."
            )
        return self


class ChecklistTriagem(BaseModel):
    """Consolida as verificacoes obrigatorias da triagem do levantamento.

    Regras de negocio:
    - Projetos de clandestinos exigem informacoes especificas para CQT dedicado.
    - Projetos nao clandestinos que receberam leitura de trafo maxima devem informar
      corrente e carga maxima lidas em campo.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    tipo_projeto: TipoProjeto
    recebeu_leitura_trafo_maxima: bool = False
    corrente_trafo_a: float | None = Field(default=None, gt=0)
    carga_maxima_transformador_kva: float | None = Field(default=None, gt=0)
    possui_fotos_campo: bool = False
    comparou_com_street_view: bool = False
    comparou_com_desenho_recebido: bool = False
    recuperacao_clandestino_confirmada: bool | None = None
    quantidade_ligacoes_irregulares: int | None = Field(default=None, ge=1)
    observacoes: str | None = Field(default=None, max_length=1000)

    @property
    def exige_cqt_clandestino(self) -> bool:
        """Indica se a triagem deve seguir o fluxo especial de clandestinos."""

        return self.tipo_projeto is TipoProjeto.CLANDESTINOS

    @model_validator(mode="after")
    def validar_regras_de_triagem(self) -> "ChecklistTriagem":
        if self.tipo_projeto is TipoProjeto.CLANDESTINOS:
            if self.recuperacao_clandestino_confirmada is None:
                raise ValueError(
                    "Checklist de clandestinos exige confirmacao de recuperacao de clandestino."
                )
            if self.quantidade_ligacoes_irregulares is None:
                raise ValueError(
                    "Checklist de clandestinos exige a quantidade de ligacoes irregulares."
                )
            if self.recebeu_leitura_trafo_maxima:
                raise ValueError(
                    "Projeto de clandestinos nao deve depender da flag de leitura maxima do trafo na triagem."
                )
        else:
            if self.recuperacao_clandestino_confirmada is not None:
                raise ValueError(
                    "Campos especificos de clandestino nao podem ser preenchidos em outros tipos de projeto."
                )
            if self.quantidade_ligacoes_irregulares is not None:
                raise ValueError(
                    "Quantidade de ligacoes irregulares so pode ser usada para projetos de clandestinos."
                )
            if self.recebeu_leitura_trafo_maxima:
                if self.corrente_trafo_a is None or self.carga_maxima_transformador_kva is None:
                    raise ValueError(
                        "Leitura maxima do trafo exige corrente e carga maxima do transformador."
                    )

        return self


class Projeto(BaseModel):
    """Representa o projeto em triagem com evidencias e checklist consolidado.

    Esta entidade e a porta de entrada do fluxo de dominio. Ela nao conhece banco,
    filas, APIs ou qualquer detalhe de persistencia.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID = Field(default_factory=uuid4)
    codigo: str = Field(min_length=3, max_length=100)
    nome: str = Field(min_length=3, max_length=200)
    localidade: str = Field(min_length=3, max_length=200)
    etapa_atual: EtapaProjeto = EtapaProjeto.TRIAGEM
    checklist_triagem: ChecklistTriagem
    evidencias: tuple[Evidencia, ...] = Field(default_factory=tuple)
    criado_em: datetime = Field(default_factory=utc_now)
