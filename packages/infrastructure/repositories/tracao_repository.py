"""Repositorio de persistencia da tracao poste a poste vinculada ao projeto."""

from __future__ import annotations

from collections.abc import Sequence
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.domain.tracao.models import Poste, ResultadoTracao
from packages.infrastructure.database.models import PosteTracaoORM, ProjetoORM, ResultadoTracaoORM


class TracaoRepository:
    """Persiste postes e resultados de tracao sem vazar ORM para o dominio."""

    def __init__(self, session: Session) -> None:
        self._session = session

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
        projeto = self._session.get(ProjetoORM, str(projeto_id))
        if projeto is None:
            raise ValueError("Projeto nao encontrado para vincular resultados de tracao.")

        resultados: list[ResultadoTracao] = []
        for poste, resultado in lista_postes_com_resultados:
            poste_orm = PosteTracaoORM(
                id=str(poste.id),
                projeto_id=str(projeto_id),
                codigo=poste.codigo,
                resistencia_nominal_daN=poste.resistencia_nominal_daN,
                vaos_json=[vao.model_dump(mode="json") for vao in poste.vaos],
            )

            resultado_orm = ResultadoTracaoORM(
                id=str(resultado.id),
                esforco_resultante_daN=resultado.esforco_resultante_daN,
                percentual_carregamento=resultado.percentual_carregamento,
                estado_mecanico=resultado.estado_mecanico.value,
                calculado_em=resultado.calculado_em,
            )
            poste_orm.resultado = resultado_orm

            self._session.add(poste_orm)
            resultados.append(resultado)

        return resultados

    def listar_resultados_por_projeto(self, projeto_id: UUID) -> list[dict]:
        """Retorna resultados de tracao persistidos para uso na exportacao."""
        rows = self._session.execute(
            select(PosteTracaoORM, ResultadoTracaoORM)
            .join(ResultadoTracaoORM, ResultadoTracaoORM.poste_id == PosteTracaoORM.id)
            .where(PosteTracaoORM.projeto_id == str(projeto_id))
            .order_by(PosteTracaoORM.codigo)
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
