"""Rota HTTP para importacao de ficheiros DXF via upload."""

from __future__ import annotations

import tempfile
from collections.abc import Callable
from pathlib import Path
from uuid import UUID

import ezdxf
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, status
from sqlalchemy.orm import Session

from apps.api.core.security import require_write_access
from apps.api.schemas.cad_schemas import ImportacaoDxfResponse
from packages.application.use_cases.cad_use_cases import ImportarArquivoDxfUseCase

router = APIRouter(tags=["cad"])


def get_session_factory(request: Request) -> Callable[[], Session]:
    """Obtém a fábrica de sessão configurada no estado da aplicação."""

    return request.app.state.session_factory


@router.post(
    "/projetos/{projeto_id}/dxf",
    response_model=ImportacaoDxfResponse,
    status_code=status.HTTP_200_OK,
    summary="Importar ficheiro DXF",
    description=(
        "Recebe um ficheiro DXF via upload, extrai as geometrias 2.5D e "
        "persiste o resultado vinculado ao projeto. Retorna um sumário com "
        "contagens de layers e segmentos válidos — sem coordenadas brutas."
    ),
)
def importar_dxf(
    projeto_id: UUID,
    file: UploadFile,
    session_factory: Callable[[], Session] = Depends(get_session_factory),
    _: object = Depends(require_write_access),
) -> ImportacaoDxfResponse:
    """Processa o upload, delega ao use case e retorna o sumário CAD."""

    # Persiste o conteúdo do upload em ficheiro temporário para que o adaptador
    # ezdxf possa abrir por caminho de disco.  O bloco finally garante a remoção
    # mesmo em caso de exceção.
    tmp_path: str | None = None
    try:
        extensao_upload = Path(file.filename or "upload.dxf").suffix.lower()
        if extensao_upload != ".dxf":
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Formato de ficheiro invalido. Envie um DXF valido.",
            )

        sufixo = Path(file.filename or "upload.dxf").suffix or ".dxf"
        with tempfile.NamedTemporaryFile(suffix=sufixo, delete=False) as tmp:
            tmp.write(file.file.read())
            tmp_path = tmp.name

        use_case = ImportarArquivoDxfUseCase(session_factory=session_factory)
        arquivo_dxf = use_case.executar(
            projeto_id=projeto_id,
            caminho_arquivo=tmp_path,
            nome_arquivo=file.filename or "upload.dxf",
        )

    except ValueError as exc:
        message = str(exc)
        code = (
            status.HTTP_404_NOT_FOUND
            if "nao encontrado" in message.lower()
            else status.HTTP_400_BAD_REQUEST
        )
        raise HTTPException(status_code=code, detail=message) from exc
    except (ezdxf.DXFError, OSError, UnicodeError) as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Formato de ficheiro invalido. Envie um DXF valido.",
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Nao foi possivel processar o ficheiro enviado.",
        ) from exc
    finally:
        if tmp_path is not None:
            Path(tmp_path).unlink(missing_ok=True)

    return ImportacaoDxfResponse.from_domain(arquivo_dxf)
