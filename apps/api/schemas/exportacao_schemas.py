"""DTOs versionados do contrato de API para geracao de pacote tecnico."""

from __future__ import annotations

from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict

from packages.domain.exportacao.models import PacoteEntrega


class StatusExportacaoDTO(str, Enum):
    """Status de exportacao exposto no contrato HTTP."""

    PENDENTE = "PENDENTE"
    PROCESSANDO = "PROCESSANDO"
    CONCLUIDO = "CONCLUIDO"
    ERRO = "ERRO"


class PacoteEntregaDTO(BaseModel):
    """DTO dos metadados de exportacao do pacote final."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    projeto_id: UUID
    status: StatusExportacaoDTO
    caminho_arquivo: str | None
    arquivos_contidos: list[str]
    mensagem_erro: str | None

    @classmethod
    def from_domain(cls, pacote: PacoteEntrega) -> "PacoteEntregaDTO":
        return cls.model_validate(
            {
                "id": pacote.id,
                "projeto_id": pacote.projeto_id,
                "status": pacote.status.value,
                "caminho_arquivo": pacote.caminho_arquivo,
                "arquivos_contidos": list(pacote.arquivos_contidos),
                "mensagem_erro": pacote.mensagem_erro,
            }
        )


class GerarPacoteResponse(BaseModel):
    """Resposta da operacao de geracao do pacote tecnico."""

    model_config = ConfigDict(extra="forbid")

    pacote: PacoteEntregaDTO
