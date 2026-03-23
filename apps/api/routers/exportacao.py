"""Rotas HTTP para geracao e download do pacote tecnico."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from apps.api.core.security import get_current_user, require_write_access
from apps.api.schemas.exportacao_schemas import GerarPacoteResponse, PacoteEntregaDTO
from packages.application.use_cases.exportacao_use_cases import GerarPacoteFinalUseCase
from packages.domain.exportacao.models import StatusExportacao
from packages.infrastructure.repositories.exportacao_repository import ExportacaoRepository

router = APIRouter(tags=["exportacao"])


def get_session_factory(request: Request) -> Callable[[], Session]:
    """Obtem a fabrica de sessao configurada no estado da aplicacao."""

    return request.app.state.session_factory


@router.post(
    "/projetos/{projeto_id}/exportacao/gerar",
    response_model=GerarPacoteResponse,
    status_code=status.HTTP_200_OK,
)
def gerar_pacote_exportacao(
    projeto_id: UUID,
    session_factory: Callable[[], Session] = Depends(get_session_factory),
    _: object = Depends(require_write_access),
) -> GerarPacoteResponse:
    """Gera Excel, PDF e ZIP final para o projeto informado."""

    use_case = GerarPacoteFinalUseCase(session_factory=session_factory)
    try:
        pacote = use_case.executar(projeto_id)
    except ValueError as exc:
        message = str(exc)
        code = status.HTTP_404_NOT_FOUND if "nao encontrado" in message.lower() else status.HTTP_400_BAD_REQUEST
        raise HTTPException(status_code=code, detail=message) from exc

    return GerarPacoteResponse(pacote=PacoteEntregaDTO.from_domain(pacote))


@router.get(
    "/projetos/{projeto_id}/exportacao/download",
    status_code=status.HTTP_200_OK,
)
def download_pacote_exportacao(
    projeto_id: UUID,
    session_factory: Callable[[], Session] = Depends(get_session_factory),
    _: object = Depends(get_current_user),
) -> FileResponse:
    """Realiza download do ZIP final quando o pacote estiver concluido."""

    with session_factory() as session:
        repository = ExportacaoRepository(session)
        pacote = repository.buscar_pacote_entrega_por_projeto(projeto_id)

    if pacote is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Pacote de entrega nao encontrado.")

    if pacote.status is not StatusExportacao.CONCLUIDO or not pacote.caminho_arquivo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Pacote de entrega ainda nao esta concluido.")

    caminho_zip = Path(pacote.caminho_arquivo)
    if not caminho_zip.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Ficheiro ZIP nao encontrado no disco.")

    return FileResponse(
        path=str(caminho_zip),
        media_type="application/zip",
        filename=caminho_zip.name,
    )
