"""Entidades de workflow e governanca do projeto."""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


def utc_now() -> datetime:
    """Padroniza timestamps do workflow em UTC."""

    return datetime.now(timezone.utc)


class EtapaProjeto(str, Enum):
    """Define as etapas macro do fluxo operacional do projeto."""

    TRIAGEM = "Triagem"
    CQT = "CQT"
    CAD = "CAD"
    TRACAO = "Tracao"
    EXPORTACAO = "Exportacao"


class HistoricoAuditoria(BaseModel):
    """Registra eventos relevantes de transicao e governanca do projeto.

    Cada evento deve indicar o projeto afetado, a etapa destino, o responsavel e
    uma descricao objetiva da acao executada.
    """

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID = Field(default_factory=uuid4)
    projeto_id: UUID
    etapa_origem: EtapaProjeto | None = None
    etapa_destino: EtapaProjeto
    acao: str = Field(min_length=3, max_length=200)
    responsavel: str = Field(min_length=3, max_length=120)
    justificativa: str | None = Field(default=None, max_length=1000)
    ocorrido_em: datetime = Field(default_factory=utc_now)

    @model_validator(mode="after")
    def validar_transicao(self) -> "HistoricoAuditoria":
        if self.etapa_origem is self.etapa_destino:
            raise ValueError("A etapa de origem deve ser diferente da etapa de destino.")
        return self
