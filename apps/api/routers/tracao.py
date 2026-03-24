"""Rotas HTTP para execucao do motor de tracao."""

from __future__ import annotations

import io
from uuid import UUID

import openpyxl
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import ValidationError

from apps.api.core.deps import get_session_factory
from apps.api.core.security import require_write_access
from apps.api.schemas.tracao_schemas import (
    CalcularTracaoRequest,
    CalcularTracaoResponse,
    ResultadoTracaoDTO,
)
from packages.application.use_cases.tracao_use_cases import CalcularTracaoProjetoUseCase
from packages.domain.tests.excel_parity_support import (
    extract_tracao,
    find_sheet_with_keywords,
)

router = APIRouter(tags=["tracao"])


def _to_num_str(value: object) -> str:
    if value is None:
        return ""
    return str(value)


def _to_travessia_mt(item) -> dict[str, str]:
    return {
        "tipoRede": _to_num_str(item.tipo_rede),
        "tipoCabo": _to_num_str(item.tipo_cabo),
        "vao": _to_num_str(item.vao),
        "flecha": _to_num_str(item.flecha),
        "angulo": _to_num_str(item.angulo),
        "alturaPoste": _to_num_str(item.altura_poste),
        "alturaAncoragem": _to_num_str(item.altura_ancoragem),
        "qtdCabos": "",
        "qtdLigacoes": "",
    }


def _to_travessia_ral(item) -> dict[str, str]:
    return {
        "tipoRede": "",
        "tipoCabo": _to_num_str(item.tipo_cabo),
        "vao": _to_num_str(item.vao),
        "flecha": _to_num_str(item.flecha),
        "angulo": _to_num_str(item.angulo),
        "alturaPoste": _to_num_str(item.altura_poste),
        "alturaAncoragem": _to_num_str(item.altura_ancoragem),
        "qtdCabos": _to_num_str(item.qtd_cabos),
        "qtdLigacoes": "",
    }


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


@router.post(
    "/importar-excel",
    status_code=status.HTTP_200_OK,
)
@router.post(
    "/tracao/importar-excel",
    status_code=status.HTTP_200_OK,
)
async def importar_excel_tracao(
    file: UploadFile = File(...),
    _: object = Depends(require_write_access),
) -> dict:
    """Importa uma planilha legada de tracao e devolve estado pronto para o frontend."""

    filename = (file.filename or "").lower()
    if not (filename.endswith(".xlsm") or filename.endswith(".xlsx")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Formato invalido. Envie um arquivo .xlsm ou .xlsx.",
        )

    raw = await file.read()
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Arquivo vazio.",
        )

    wb = None
    try:
        wb = openpyxl.load_workbook(io.BytesIO(raw), data_only=True, read_only=False)
        ws = find_sheet_with_keywords(wb, "TRACAO TOTAL")
        if ws is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Nao foi encontrada aba de Tracao no arquivo enviado.",
            )
        parsed = extract_tracao(ws)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Falha ao ler a planilha: {exc}",
        ) from exc
    finally:
        try:
            wb.close()
        except Exception:
            pass

    return {
        "dadosPoste": {
            "orgao": "",
            "ns": "",
            "projeto": "",
            "ponto": "01",
            "matricula": "",
            "data": "",
            "tipoPoste": parsed.tipo_poste,
            "modeloPoste": parsed.modelo_poste,
            "coordenadas": "",
        },
        "secoes": {
            "mt1": [_to_travessia_mt(item) for item in parsed.mt1],
            "mt2": [_to_travessia_mt(item) for item in parsed.mt2],
            "bt": [_to_travessia_mt(item) for item in parsed.bt],
            "ral": [_to_travessia_ral(item) for item in parsed.ral],
        },
    }
