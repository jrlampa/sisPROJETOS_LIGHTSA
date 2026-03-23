"""Rotas de intake e workflow de projetos."""

from __future__ import annotations

import logging
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status

from apps.api.core.deps import get_session_factory
from apps.api.core.security import require_write_access
from apps.api.schemas.projeto_schemas import (
    AvancarEtapaRequest,
    AvancarEtapaResponse,
    HistoricoAuditoriaResponse,
    ProjetoCreateRequest,
    ProjetoResponse,
)
from packages.application.use_cases.projeto_use_cases import (
    AvancarEtapaUseCase,
    CriarProjetoUseCase,
)
from packages.domain.workflow.models import EtapaProjeto

router = APIRouter(prefix="/projetos", tags=["projetos"])
logger = logging.getLogger(__name__)


@router.post("/", response_model=ProjetoResponse, status_code=status.HTTP_201_CREATED)
def criar_projeto(
    payload: ProjetoCreateRequest,
    session_factory=Depends(get_session_factory),
    _: object = Depends(require_write_access),
) -> ProjetoResponse:
    """Cria um projeto validando regras de dominio via caso de uso."""

    use_case = CriarProjetoUseCase(session_factory=session_factory)
    try:
        projeto = use_case.executar(payload.model_dump(mode="json", exclude_none=True))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    logger.info("Projeto criado com sucesso: projeto_id=%s", projeto.id)
    return ProjetoResponse.from_domain(projeto)


@router.patch("/{projeto_id}/etapa", response_model=AvancarEtapaResponse)
def avancar_etapa(
    projeto_id: UUID,
    payload: AvancarEtapaRequest,
    session_factory=Depends(get_session_factory),
    _: object = Depends(require_write_access),
) -> AvancarEtapaResponse:
    """Avança a etapa do projeto e registra evento de auditoria."""

    use_case = AvancarEtapaUseCase(session_factory=session_factory)
    try:
        projeto_atualizado, historico = use_case.executar(
            projeto_id=projeto_id,
            nova_etapa=EtapaProjeto(payload.nova_etapa.value),
            responsavel=payload.responsavel,
            justificativa=payload.justificativa,
        )
    except ValueError as exc:
        message = str(exc)
        code = (
            status.HTTP_404_NOT_FOUND
            if "nao encontrado" in message.lower()
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=code, detail=message) from exc

    return AvancarEtapaResponse(
        projeto=ProjetoResponse.from_domain(projeto_atualizado),
        historico=HistoricoAuditoriaResponse.from_domain(historico),
    )
