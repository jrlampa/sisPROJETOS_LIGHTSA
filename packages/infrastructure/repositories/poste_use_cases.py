"""Casos de uso relacionados à entidade Poste."""

from __future__ import annotations

from uuid import UUID

from packages.application.query_models import (
    PosteConsolidado,
    ResultadoTracaoResumo,
    TrechoConectado,
)
from packages.infrastructure.repositories.poste_repository import PosteRepository


class ObterPosteConsolidadoUseCase:
    """Caso de uso para obter a visão 360º de um poste."""

    def __init__(self, session_factory):
        self.session_factory = session_factory

    def executar(self, projeto_id: UUID, poste_codigo: str) -> PosteConsolidado:
        """
        Executa a busca e a consolidação dos dados do poste.

        Raises:
            ValueError: Se o poste não for encontrado.
        """
        with self.session_factory() as session:
            repo = PosteRepository(session)
            poste_orm = repo.find_consolidado_by_codigo(projeto_id, poste_codigo)

            if poste_orm is None:
                raise ValueError(f"Poste com código '{poste_codigo}' não encontrado no projeto.")

            # Constrói a lista de trechos conectados
            trechos_conectados = []
            for trecho_orm in poste_orm.trechos_de:  # Trechos que saem deste poste
                trechos_conectados.append(
                    TrechoConectado(
                        id=trecho_orm.id,
                        nome=f"{poste_orm.codigo}-{trecho_orm.poste_para.codigo}",
                        tipo_conexao="de",
                        condutor_nome=trecho_orm.condutor.nome,
                        comprimento_m=trecho_orm.comprimento_m,
                    )
                )
            for trecho_orm in poste_orm.trechos_para:  # Trechos que chegam neste poste
                trechos_conectados.append(
                    TrechoConectado(
                        id=trecho_orm.id,
                        nome=f"{trecho_orm.poste_de.codigo}-{poste_orm.codigo}",
                        tipo_conexao="para",
                        condutor_nome=trecho_orm.condutor.nome,
                        comprimento_m=trecho_orm.comprimento_m,
                    )
                )

            # Constrói o resumo do resultado de tração
            resultado_resumo = None
            if poste_orm.resultado:
                resultado_resumo = ResultadoTracaoResumo.model_validate(poste_orm.resultado)

            return PosteConsolidado(
                id=poste_orm.id,
                codigo=poste_orm.codigo,
                resistencia_nominal_daN=poste_orm.resistencia_nominal_daN,
                resultado_tracao=resultado_resumo,
                trechos_conectados=trechos_conectados,
            )