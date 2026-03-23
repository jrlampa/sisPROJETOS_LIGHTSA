"""Testes unitarios do dominio de exportacao e relatorios."""

from __future__ import annotations

from uuid import uuid4

import pytest
from pydantic import ValidationError

from packages.domain.exportacao.models import (
    ExportacaoExcel,
    PacoteEntrega,
    RelatorioTecnico,
    StatusExportacao,
)


def test_relatorio_tecnico_inicia_pendente() -> None:
    relatorio = RelatorioTecnico(projeto_id=uuid4())

    assert relatorio.status is StatusExportacao.PENDENTE
    assert relatorio.caminho_arquivo is None
    assert relatorio.mensagem_erro is None


def test_relatorio_tecnico_marca_concluido() -> None:
    relatorio = RelatorioTecnico(projeto_id=uuid4())

    concluido = relatorio.marcar_como_concluido("saida/relatorio_tecnico.pdf")

    assert concluido.status is StatusExportacao.CONCLUIDO
    assert concluido.caminho_arquivo == "saida/relatorio_tecnico.pdf"
    assert concluido.mensagem_erro is None


def test_relatorio_tecnico_marca_erro() -> None:
    relatorio = RelatorioTecnico(projeto_id=uuid4())

    com_erro = relatorio.marcar_como_erro("Falha ao gerar PDF.")

    assert com_erro.status is StatusExportacao.ERRO
    assert com_erro.mensagem_erro == "Falha ao gerar PDF."


def test_exportacao_excel_inicia_pendente_com_tipo_default() -> None:
    excel = ExportacaoExcel(projeto_id=uuid4())

    assert excel.status is StatusExportacao.PENDENTE
    assert excel.tipo_planilha == "CQT_NORMAL"


def test_exportacao_excel_marca_concluido() -> None:
    excel = ExportacaoExcel(projeto_id=uuid4(), tipo_planilha="CQT_CLANDESTINO")

    concluido = excel.marcar_como_concluido("saida/cqt_clandestino.xlsx")

    assert concluido.status is StatusExportacao.CONCLUIDO
    assert concluido.caminho_arquivo == "saida/cqt_clandestino.xlsx"


def test_exportacao_excel_marca_erro() -> None:
    excel = ExportacaoExcel(projeto_id=uuid4())

    com_erro = excel.marcar_como_erro("Template nao encontrado.")

    assert com_erro.status is StatusExportacao.ERRO
    assert com_erro.mensagem_erro == "Template nao encontrado."


def test_pacote_entrega_inicia_pendente_sem_arquivos() -> None:
    pacote = PacoteEntrega(projeto_id=uuid4())

    assert pacote.status is StatusExportacao.PENDENTE
    assert pacote.arquivos_contidos == ()


def test_pacote_entrega_marca_concluido_com_lista_de_arquivos() -> None:
    pacote = PacoteEntrega(projeto_id=uuid4())

    concluido = pacote.marcar_como_concluido(
        caminho="saida/pacote_final.zip",
        arquivos_contidos=(
            "saida/relatorio_tecnico.pdf",
            "saida/cqt_normal.xlsx",
            "saida/geometria.dxf",
        ),
    )

    assert concluido.status is StatusExportacao.CONCLUIDO
    assert concluido.caminho_arquivo == "saida/pacote_final.zip"
    assert len(concluido.arquivos_contidos) == 3


def test_pacote_entrega_marca_erro() -> None:
    pacote = PacoteEntrega(projeto_id=uuid4())

    com_erro = pacote.marcar_como_erro("Nao foi possivel compactar os artefatos.")

    assert com_erro.status is StatusExportacao.ERRO
    assert com_erro.mensagem_erro == "Nao foi possivel compactar os artefatos."


def test_validacao_rejeita_concluido_sem_caminho() -> None:
    with pytest.raises(ValidationError, match="concluido exige caminho_arquivo"):
        RelatorioTecnico(projeto_id=uuid4(), status=StatusExportacao.CONCLUIDO)


def test_validacao_rejeita_erro_sem_mensagem() -> None:
    with pytest.raises(ValidationError, match="com erro exige mensagem_erro"):
        PacoteEntrega(projeto_id=uuid4(), status=StatusExportacao.ERRO)
