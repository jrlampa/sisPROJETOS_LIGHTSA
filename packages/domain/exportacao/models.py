"""Entidades e regras puras para controle de exportacoes e relatorios."""

from __future__ import annotations

from enum import Enum
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StatusExportacao(str, Enum):
    """Estados do ciclo de vida de geracao de artefatos de exportacao."""

    PENDENTE = "PENDENTE"
    PROCESSANDO = "PROCESSANDO"
    CONCLUIDO = "CONCLUIDO"
    ERRO = "ERRO"


class RelatorioTecnico(BaseModel):
    """Metadados de controle do relatorio tecnico em PDF."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID = Field(default_factory=uuid4)
    projeto_id: UUID
    status: StatusExportacao = StatusExportacao.PENDENTE
    caminho_arquivo: str | None = Field(default=None, min_length=3, max_length=500)
    mensagem_erro: str | None = Field(default=None, min_length=3, max_length=1000)

    @model_validator(mode="after")
    def validar_consistencia_estado(self) -> "RelatorioTecnico":
        if self.status is StatusExportacao.CONCLUIDO and not self.caminho_arquivo:
            raise ValueError("Relatorio concluido exige caminho_arquivo preenchido.")
        if self.status is StatusExportacao.ERRO and not self.mensagem_erro:
            raise ValueError("Relatorio com erro exige mensagem_erro preenchida.")
        return self

    def marcar_como_processando(self) -> "RelatorioTecnico":
        return self.model_copy(
            update={
                "status": StatusExportacao.PROCESSANDO,
                "mensagem_erro": None,
            }
        )

    def marcar_como_concluido(self, caminho: str) -> "RelatorioTecnico":
        return self.model_copy(
            update={
                "status": StatusExportacao.CONCLUIDO,
                "caminho_arquivo": caminho,
                "mensagem_erro": None,
            }
        )

    def marcar_como_erro(self, mensagem: str) -> "RelatorioTecnico":
        return self.model_copy(
            update={
                "status": StatusExportacao.ERRO,
                "mensagem_erro": mensagem,
            }
        )


class ExportacaoExcel(BaseModel):
    """Metadados de controle da exportacao de planilha Excel."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID = Field(default_factory=uuid4)
    projeto_id: UUID
    tipo_planilha: str = Field(default="CQT_NORMAL", min_length=3, max_length=80)
    status: StatusExportacao = StatusExportacao.PENDENTE
    caminho_arquivo: str | None = Field(default=None, min_length=3, max_length=500)
    mensagem_erro: str | None = Field(default=None, min_length=3, max_length=1000)

    @model_validator(mode="after")
    def validar_consistencia_estado(self) -> "ExportacaoExcel":
        if self.status is StatusExportacao.CONCLUIDO and not self.caminho_arquivo:
            raise ValueError("Exportacao Excel concluida exige caminho_arquivo preenchido.")
        if self.status is StatusExportacao.ERRO and not self.mensagem_erro:
            raise ValueError("Exportacao Excel com erro exige mensagem_erro preenchida.")
        return self

    def marcar_como_processando(self) -> "ExportacaoExcel":
        return self.model_copy(
            update={
                "status": StatusExportacao.PROCESSANDO,
                "mensagem_erro": None,
            }
        )

    def marcar_como_concluido(self, caminho: str) -> "ExportacaoExcel":
        return self.model_copy(
            update={
                "status": StatusExportacao.CONCLUIDO,
                "caminho_arquivo": caminho,
                "mensagem_erro": None,
            }
        )

    def marcar_como_erro(self, mensagem: str) -> "ExportacaoExcel":
        return self.model_copy(
            update={
                "status": StatusExportacao.ERRO,
                "mensagem_erro": mensagem,
            }
        )


class PacoteEntrega(BaseModel):
    """Agregado de controle do pacote ZIP final de entrega."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    id: UUID = Field(default_factory=uuid4)
    projeto_id: UUID
    status: StatusExportacao = StatusExportacao.PENDENTE
    arquivos_contidos: tuple[str, ...] = Field(default_factory=tuple)
    caminho_arquivo: str | None = Field(default=None, min_length=3, max_length=500)
    mensagem_erro: str | None = Field(default=None, min_length=3, max_length=1000)

    @model_validator(mode="after")
    def validar_consistencia_estado(self) -> "PacoteEntrega":
        if self.status is StatusExportacao.CONCLUIDO and not self.caminho_arquivo:
            raise ValueError("Pacote de entrega concluido exige caminho_arquivo preenchido.")
        if self.status is StatusExportacao.ERRO and not self.mensagem_erro:
            raise ValueError("Pacote de entrega com erro exige mensagem_erro preenchida.")
        return self

    def marcar_como_processando(self) -> "PacoteEntrega":
        return self.model_copy(
            update={
                "status": StatusExportacao.PROCESSANDO,
                "mensagem_erro": None,
            }
        )

    def marcar_como_concluido(self, caminho: str, arquivos_contidos: tuple[str, ...]) -> "PacoteEntrega":
        return self.model_copy(
            update={
                "status": StatusExportacao.CONCLUIDO,
                "caminho_arquivo": caminho,
                "arquivos_contidos": arquivos_contidos,
                "mensagem_erro": None,
            }
        )

    def marcar_como_erro(self, mensagem: str) -> "PacoteEntrega":
        return self.model_copy(
            update={
                "status": StatusExportacao.ERRO,
                "mensagem_erro": mensagem,
            }
        )
