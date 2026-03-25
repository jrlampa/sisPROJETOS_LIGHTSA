"""Entidades e regras puras da base espacial CAD em 2.5D."""

from __future__ import annotations

from datetime import datetime, timezone
from math import hypot
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator


def utc_now() -> datetime:
    """Padroniza timestamps de entidades CAD em UTC."""

    return datetime.now(timezone.utc)


class Ponto(BaseModel):
    """Representa um ponto espacial em 2.5D.

    O eixo Z e mantido para elevação/cota, porém os cálculos de distância desta
    fase consideram apenas o plano XY.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    x: float
    y: float
    z: float = 0.0


class Segmento(BaseModel):
    """Representa um segmento entre dois pontos.

    Regra de negócio: não existe segmento de comprimento zero.
    O comprimento é calculado no plano XY (2D), ignorando diferença no eixo Z.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID = Field(default_factory=uuid4)
    ponto_inicial: Ponto
    ponto_final: Ponto

    @model_validator(mode="after")
    def validar_comprimento_positivo(self) -> "Segmento":
        if (
            self.ponto_inicial.x == self.ponto_final.x
            and self.ponto_inicial.y == self.ponto_final.y
            and self.ponto_inicial.z == self.ponto_final.z
        ):
            raise ValueError("Segmento invalido: ponto inicial e final nao podem ser identicos.")
        if self.comprimento_plano_xy == 0:
            raise ValueError("Segmento invalido: comprimento no plano XY deve ser maior que zero.")
        return self

    @computed_field
    @property
    def comprimento_plano_xy(self) -> float:
        """Calcula a distância plana XY."""

        delta_x = self.ponto_final.x - self.ponto_inicial.x
        delta_y = self.ponto_final.y - self.ponto_inicial.y
        return hypot(delta_x, delta_y)


class LayerTecnica(BaseModel):
    """Representa uma camada técnica de desenho no padrão CAD."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID = Field(default_factory=uuid4)
    nome: str = Field(min_length=2, max_length=120)
    cor_autocad: int = Field(ge=1, le=255)


class GeometriaProjeto(BaseModel):
    """Agrupa segmentos por layer para representar a geometria de projeto."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID = Field(default_factory=uuid4)
    nome: str = Field(min_length=3, max_length=150)
    layer_tecnica: LayerTecnica
    segmentos: tuple[Segmento, ...] = Field(default_factory=tuple)

    @computed_field
    @property
    def comprimento_total_xy(self) -> float:
        """Soma o comprimento XY de todos os segmentos da geometria."""

        return sum(segmento.comprimento_plano_xy for segmento in self.segmentos)


class ArquivoDXF(BaseModel):
    """Representa um artefato lógico de saída/entrada DXF do projeto.

    Nesta camada de domínio, o DXF é tratado apenas como metadado e coleção
    geométrica. A leitura/escrita física ficará na infraestrutura.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID = Field(default_factory=uuid4)
    nome_arquivo: str = Field(min_length=5, max_length=260)
    versao: str = Field(default="R2018", min_length=2, max_length=20)
    geometrias: tuple[GeometriaProjeto, ...] = Field(default_factory=tuple)
    criado_em: datetime = Field(default_factory=utc_now)

    @computed_field
    @property
    def quantidade_segmentos(self) -> int:
        """Retorna o total de segmentos consolidados no arquivo lógico."""

        return sum(len(geometria.segmentos) for geometria in self.geometrias)
