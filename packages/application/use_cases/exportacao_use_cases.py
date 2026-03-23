"""Casos de uso da camada de aplicacao para relatorios e pacote final."""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from sqlalchemy.orm import Session

from packages.domain.exportacao.models import ExportacaoExcel, PacoteEntrega, RelatorioTecnico
from packages.infrastructure.adapters.exportacao_adapter import ExportadorFicheiros
from packages.infrastructure.repositories.cqt_repository import CQTRepository
from packages.infrastructure.repositories.exportacao_repository import ExportacaoRepository
from packages.infrastructure.repositories.projeto_repository import ProjetoRepository
from packages.infrastructure.repositories.tracao_repository import TracaoRepository


class GerarPacoteFinalUseCase:
    """Orquestra a geracao de Excel, PDF e ZIP final de entrega."""

    def __init__(
        self,
        session_factory: Callable[[], Session],
        adapter: ExportadorFicheiros | None = None,
        exportacao_repository: ExportacaoRepository | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._adapter = adapter
        self._exportacao_repository = exportacao_repository

    def executar(self, projeto_id: UUID) -> PacoteEntrega:
        with self._session_factory() as session:
            projeto_repository = ProjetoRepository(session)
            cqt_repository = CQTRepository(session)
            tracao_repository = TracaoRepository(session)
            exportacao_repository = self._exportacao_repository or ExportacaoRepository(session)

            projeto = projeto_repository.buscar_projeto_por_id(projeto_id)
            if projeto is None:
                raise ValueError("Projeto nao encontrado para gerar pacote final.")

            dados_cqt = cqt_repository.obter_resumo_por_projeto(projeto_id)
            if dados_cqt is None:
                raise ValueError("Analise CQT nao encontrada para gerar exportacao.")

            dados_tracao = tracao_repository.listar_resultados_por_projeto(projeto_id)
            if not dados_tracao:
                raise ValueError("Resultados de tracao nao encontrados para gerar exportacao.")

            pacote = PacoteEntrega(projeto_id=projeto_id).marcar_como_processando()
            relatorio_pdf = RelatorioTecnico(projeto_id=projeto_id).marcar_como_processando()
            exportacao_excel = ExportacaoExcel(projeto_id=projeto_id).marcar_como_processando()

            adapter = self._adapter or ExportadorFicheiros()
            caminho_excel = adapter.gerar_excel_padrao(projeto_id, dados_cqt, dados_tracao)
            caminho_pdf = adapter.gerar_pdf_tecnico(projeto_id)

            exportacao_excel = exportacao_excel.marcar_como_concluido(caminho_excel)
            relatorio_pdf = relatorio_pdf.marcar_como_concluido(caminho_pdf)

            caminho_zip = adapter.gerar_pacote_zip(
                projeto_id,
                [exportacao_excel.caminho_arquivo, relatorio_pdf.caminho_arquivo],
            )
            pacote = pacote.marcar_como_concluido(
                caminho=caminho_zip,
                arquivos_contidos=(
                    exportacao_excel.caminho_arquivo or "",
                    relatorio_pdf.caminho_arquivo or "",
                ),
            )

            exportacao_repository.salvar_pacote_entrega(pacote)
            session.commit()
            return pacote
