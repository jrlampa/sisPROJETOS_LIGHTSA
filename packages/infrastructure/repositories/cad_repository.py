"""Repositorio de persistencia da geometria CAD vinculada ao projeto."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from packages.domain.cad.models import ArquivoDXF
from packages.infrastructure.database.models import GeometriaProjetoORM, ProjetoORM


class CADRepository:
    """Persiste ArquivoDXF sem vazar ORM para a camada de dominio.

    As coordenadas sao serializadas como JSON para evitar milhares de registros
    relacionais de Ponto, mantendo performance e simplicidade.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def salvar_geometria(self, projeto_id: UUID, arquivo_dxf: ArquivoDXF) -> ArquivoDXF:
        """Persiste a geometria DXF associando-a ao projeto informado.

        Args:
            projeto_id: UUID do Projeto ao qual a geometria pertence.
            arquivo_dxf: Entidade de dominio ArquivoDXF com as geometrias.

        Returns:
            O mesmo ArquivoDXF recebido (pass-through apos persistencia).

        Raises:
            ValueError: Se o projeto_id nao corresponder a nenhum Projeto.
        """
        projeto = self._session.get(ProjetoORM, str(projeto_id))
        if projeto is None:
            raise ValueError("Projeto nao encontrado para vincular geometria CAD.")

        # Serializa a lista de GeometriaProjeto para JSON (mode="json" garante
        # que tipos como UUID e datetime sejam convertidos para tipos primitivos).
        dados_geometria = [
            geometria.model_dump(mode="json") for geometria in arquivo_dxf.geometrias
        ]

        geometria_orm = GeometriaProjetoORM(
            projeto_id=str(projeto_id),
            nome_arquivo=arquivo_dxf.nome_arquivo,
            versao_dxf=arquivo_dxf.versao,
            dados_geometria=dados_geometria,
            criado_em=arquivo_dxf.criado_em,
        )
        self._session.add(geometria_orm)
        return arquivo_dxf
