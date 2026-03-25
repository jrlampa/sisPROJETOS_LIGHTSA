"""Rotas HTTP para consulta de postes."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from apps.api.core.deps import get_session_factory
from apps.api.core.security import require_read_access
from apps.api.schemas.poste_schemas import PosteConsolidadoResponse
from packages.application.use_cases.poste_use_cases import ObterPosteConsolidadoUseCase

router = APIRouter(tags=["Postes"])


@router.get(
    "/projetos/{projeto_id}/postes/{poste_codigo}",
    response_model=PosteConsolidadoResponse,
    status_code=status.HTTP_200_OK,
)
def obter_poste_consolidado(
    projeto_id: UUID,
    poste_codigo: str,
    session_factory=Depends(get_session_factory),
    _: object = Depends(require_read_access),
) -> PosteConsolidadoResponse:
    """Obtém uma visão consolidada de um poste, com seus dados de tração e trechos elétricos."""
    use_case = ObterPosteConsolidadoUseCase(session_factory)
    try:
        poste_consolidado = use_case.executar(projeto_id, poste_codigo)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return PosteConsolidadoResponse.from_domain(poste_consolidado)