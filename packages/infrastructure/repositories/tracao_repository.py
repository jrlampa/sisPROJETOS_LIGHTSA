"""Repositorio de persistencia da tracao poste a poste vinculada ao projeto."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.domain.tracao.models import Poste, ResultadoTracao
from packages.infrastructure.database.models import PosteProjetoORM, ResultadoTracaoORM
from packages.infrastructure.repositories.base_repository import BaseRepository
from packages.infrastructure.repositories.poste_repository import PosteRepository


class TracaoRepository(BaseRepository):
    """Persiste postes e resultados de tracao sem vazar ORM para o dominio."""

    def __init__(self, session: Session) -> None:
        super().__init__(session)
        self._poste_repository = PosteRepository(session)

    def salvar_resultados_tracao(
        self,
        projeto_id: UUID,
        lista_postes_com_resultados: Sequence[tuple[Poste, ResultadoTracao]],
    ) -> list[ResultadoTracao]:
        """Persiste todos os postes e seus resultados mecanicos.

        Args:
            projeto_id: Projeto pai ao qual os postes pertencem.
            lista_postes_com_resultados: Pares (Poste, ResultadoTracao) calculados.

        Returns:
            Lista de ResultadoTracao em pass-through apos persistencia.

        Raises:
            ValueError: Se o projeto nao existir.
        """
        self._get_projeto_orm(
            projeto_id, "Projeto nao encontrado para vincular resultados de tracao."
        )

        resultados: list[ResultadoTracao] = []
        postes_orm_cache: dict[str, PosteProjetoORM] = {}

        for poste, resultado in lista_postes_com_resultados:
            # 1. Delega a criação/busca do Poste para o repositório dedicado
            poste_orm = self._poste_repository.get_or_create(projeto_id, poste, postes_orm_cache)

            # 2. A responsabilidade do TracaoRepository é salvar o RESULTADO do cálculo
            resultado_orm = ResultadoTracaoORM(
                id=str(resultado.id),
                esforco_resultante_daN=resultado.esforco_resultante_daN,
                percentual_carregamento=resultado.percentual_carregamento,
                estado_mecanico=resultado.estado_mecanico.value,
                calculado_em=resultado.calculado_em,
            )
            poste_orm.resultado = resultado_orm

            resultados.append(resultado)

        return resultados

    def listar_resultados_por_projeto(self, projeto_id: UUID) -> list[dict]:
        """Retorna resultados de tracao persistidos para uso na exportacao."""
        rows = self._session.execute(
            select(PosteProjetoORM, ResultadoTracaoORM)
            .join(ResultadoTracaoORM, ResultadoTracaoORM.poste_id == PosteProjetoORM.id)
            .where(PosteProjetoORM.projeto_id == str(projeto_id))
            .order_by(PosteProjetoORM.codigo)
        ).all()

        return [
            {
                "poste_codigo": poste.codigo,
                "esforco_resultante_daN": resultado.esforco_resultante_daN,
                "percentual_carregamento": resultado.percentual_carregamento,
                "estado_mecanico": resultado.estado_mecanico,
            }
            for poste, resultado in rows
        ]
