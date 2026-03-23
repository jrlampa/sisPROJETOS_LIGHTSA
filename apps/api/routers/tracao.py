"""Rotas HTTP para execucao do motor de tracao."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import ValidationError

from apps.api.core.deps import get_session_factory
from apps.api.core.security import require_write_access
from apps.api.schemas.tracao_schemas import (
    CalcularTracaoRequest,
    CalcularTracaoResponse,
    ResultadoTracaoDTO,
)
from packages.application.use_cases.tracao_use_cases import CalcularTracaoProjetoUseCase

router = APIRouter(tags=["tracao"])


@router.post(
    "/projetos/{projeto_id}/tracao",
    response_model=CalcularTracaoResponse,
    status_code=status.HTTP_200_OK,
)
def calcular_tracao_projeto(
    projeto_id: UUID,
    payload: CalcularTracaoRequest,
    session_factory=Depends(get_session_factory),
    _: object = Depends(require_write_access),
) -> CalcularTracaoResponse:
    """Calcula e persiste os resultados mecanicos de tracao do projeto."""

    use_case = CalcularTracaoProjetoUseCase(session_factory=session_factory)
    try:
        resultados = use_case.executar(
            projeto_id=projeto_id,
            dados_brutos_postes=[poste.model_dump(mode="json") for poste in payload.postes],
        )
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ValueError as exc:
        message = str(exc)
        code = (
            status.HTTP_404_NOT_FOUND
            if "nao encontrado" in message.lower()
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=code, detail=message) from exc

    return CalcularTracaoResponse(
        resultados=[ResultadoTracaoDTO.from_domain(item) for item in resultados]
    )
