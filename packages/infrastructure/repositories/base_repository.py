"""Classe base para repositórios com funcionalidades comuns."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from packages.infrastructure.database.models import ProjetoORM


class BaseRepository:
    """Classe base para repositórios com funcionalidades comuns de acesso a dados."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def _get_projeto_orm(self, projeto_id: UUID, error_message: str) -> ProjetoORM:
        """
        Busca a entidade ProjetoORM pelo ID, lançando uma exceção se não for encontrada.

        Args:
            projeto_id: O ID do projeto a ser buscado.
            error_message: A mensagem de erro a ser usada na exceção.
        """
        projeto = self._session.get(ProjetoORM, str(projeto_id))
        if projeto is None:
            raise ValueError(error_message)
        return projeto