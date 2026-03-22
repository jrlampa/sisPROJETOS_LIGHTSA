"""Casos de uso da camada de aplicacao para o motor CQT."""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from sqlalchemy.orm import Session

from packages.domain.cqt.models import CQTAnalise
from packages.infrastructure.repositories.cqt_repository import CQTRepository


class ExecutarAnaliseCQTUseCase:
    """Executa analise CQT e persiste o resultado vinculado ao projeto.

    Fluxo:
    1. Valida o payload bruto através da entidade de domínio CQTAnalise.
    2. Persiste o agregado CQT na camada de infraestrutura.
    """

    def __init__(
        self,
        session_factory: Callable[[], Session],
        repository: CQTRepository | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._repository = repository

    def executar(self, projeto_id: UUID, dados_brutos_cqt: dict) -> CQTAnalise:
        analise = CQTAnalise.model_validate(dados_brutos_cqt)
        with self._session_factory() as session:
            repository = self._repository or CQTRepository(session)
            resultado = repository.salvar_analise_cqt(projeto_id, analise)
            session.commit()
            return resultado
