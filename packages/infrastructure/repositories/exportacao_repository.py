"""Repositorio de persistencia dos metadados do pacote final de entrega."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from packages.domain.exportacao.models import PacoteEntrega
from packages.infrastructure.database.models import PacoteEntregaORM, ProjetoORM


class ExportacaoRepository:
    """Persiste artefatos de exportacao sem vazar ORM para o dominio."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def salvar_pacote_entrega(self, pacote: PacoteEntrega) -> PacoteEntrega:
        """Insere ou atualiza os metadados do pacote final para o projeto."""
        projeto = self._session.get(ProjetoORM, str(pacote.projeto_id))
        if projeto is None:
            raise ValueError("Projeto nao encontrado para vincular pacote de entrega.")

        registro = self._session.get(PacoteEntregaORM, str(pacote.id))
        if registro is None:
            registro = (
                self._session.query(PacoteEntregaORM)
                .filter(PacoteEntregaORM.projeto_id == str(pacote.projeto_id))
                .one_or_none()
            )

        if registro is None:
            registro = PacoteEntregaORM(
                id=str(pacote.id),
                projeto_id=str(pacote.projeto_id),
                status=pacote.status.value,
                caminho_arquivo=pacote.caminho_arquivo,
                arquivos_contidos=list(pacote.arquivos_contidos),
                mensagem_erro=pacote.mensagem_erro,
            )
            self._session.add(registro)
        else:
            registro.status = pacote.status.value
            registro.caminho_arquivo = pacote.caminho_arquivo
            registro.arquivos_contidos = list(pacote.arquivos_contidos)
            registro.mensagem_erro = pacote.mensagem_erro

        return pacote

    def buscar_pacote_entrega_por_projeto(self, projeto_id: UUID) -> PacoteEntrega | None:
        registro = (
            self._session.query(PacoteEntregaORM)
            .filter(PacoteEntregaORM.projeto_id == str(projeto_id))
            .one_or_none()
        )
        if registro is None:
            return None

        return PacoteEntrega(
            id=UUID(registro.id),
            projeto_id=UUID(registro.projeto_id),
            status=registro.status,
            caminho_arquivo=registro.caminho_arquivo,
            arquivos_contidos=tuple(registro.arquivos_contidos or []),
            mensagem_erro=registro.mensagem_erro,
        )
