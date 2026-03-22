"""Rotas HTTP para execução do motor CQT."""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import ValidationError
from sqlalchemy.orm import Session

from apps.api.schemas.cqt_schemas import CQTAnaliseRequest, CQTAnaliseResponse
from packages.application.use_cases.cqt_use_cases import ExecutarAnaliseCQTUseCase

router = APIRouter(tags=["cqt"])


def get_session_factory(request: Request) -> Callable[[], Session]:
    """Obtém a fábrica de sessão configurada no estado da aplicação."""

    return request.app.state.session_factory


@router.post("/projetos/{projeto_id}/cqt", response_model=CQTAnaliseResponse, status_code=status.HTTP_201_CREATED)
def executar_analise_cqt(
    projeto_id: UUID,
    payload: CQTAnaliseRequest,
    session_factory: Callable[[], Session] = Depends(get_session_factory),
) -> CQTAnaliseResponse:
    """Executa análise CQT, persiste os resultados e retorna cálculos consolidados."""

    use_case = ExecutarAnaliseCQTUseCase(session_factory=session_factory)
    try:
        analise = use_case.executar(projeto_id=projeto_id, dados_brutos_cqt=payload.model_dump(mode="json", exclude_none=True))
    except ValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
    except ValueError as exc:
        message = str(exc)
        code = status.HTTP_404_NOT_FOUND if "nao encontrado" in message.lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=message) from exc

    return CQTAnaliseResponse.from_domain(analise)
