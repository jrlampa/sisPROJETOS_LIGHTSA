"""Repositório central para a entidade Poste."""

from __future__ import annotations

from uuid import UUID, uuid4

from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from packages.domain.tracao.models import Poste
from packages.infrastructure.database.models import PosteProjetoORM, TrechoEletricoORM


class PosteRepository:
    """
    Gerencia a persistência da entidade Poste, garantindo que haja uma única
    fonte de verdade para cada poste (por código) dentro de um projeto.
    """

    def __init__(self, session: Session) -> None:
        self._session = session

    def get_or_create(
        self, projeto_id: UUID, poste_domain: Poste, cache: dict[str, PosteProjetoORM]
    ) -> PosteProjetoORM:
        """
        Busca um poste no cache da transação ou o cria/atualiza.

        Se o poste já existe, seus dados (ex: resistencia) são atualizados
        com as informações do `poste_domain` (enriquecimento).
        """
        if poste_domain.codigo in cache:
            poste_orm = cache[poste_domain.codigo]
        else:
            # NOTA: Uma implementação mais robusta buscaria no banco aqui
            # para enriquecer um poste criado em outra transação.
            poste_orm = PosteProjetoORM(
                id=str(poste_domain.id),
                projeto_id=str(projeto_id),
                codigo=poste_domain.codigo,
            )
            self._session.add(poste_orm)
            cache[poste_domain.codigo] = poste_orm

        # Enriquece o ORM com dados da análise de tração
        poste_orm.resistencia_nominal_daN = poste_domain.resistencia_nominal_daN
        poste_orm.vaos_json = [vao.model_dump(mode="json") for vao in poste_domain.vaos]

        return poste_orm

    def get_or_create_stub(
        self, projeto_id: UUID, poste_codigo: str, cache: dict[str, PosteProjetoORM]
    ) -> PosteProjetoORM:
        """Busca um poste no cache ou cria um 'stub' (apenas com código)."""
        if poste_codigo in cache:
            return cache[poste_codigo]

        poste_orm = PosteProjetoORM(
            id=str(uuid4()),
            projeto_id=str(projeto_id),
            codigo=poste_codigo,
        )
        self._session.add(poste_orm)
        cache[poste_codigo] = poste_orm
        return poste_orm

    def find_consolidado_by_codigo(
        self, projeto_id: UUID, poste_codigo: str
    ) -> PosteProjetoORM | None:
        """
        Busca um poste pelo código e carrega ansiosamente (eagerly loads)
        seus dados de tração e os trechos elétricos conectados a ele.
        """
        return self._session.scalars(
            select(PosteProjetoORM)
            .options(
                selectinload(PosteProjetoORM.resultado),
                selectinload(PosteProjetoORM.trechos_de).options(
                    selectinload(TrechoEletricoORM.condutor),
                    selectinload(TrechoEletricoORM.poste_para),
                ),
                selectinload(PosteProjetoORM.trechos_para).options(
                    selectinload(TrechoEletricoORM.condutor),
                    selectinload(TrechoEletricoORM.poste_de),
                ),
            )
            .where(
                PosteProjetoORM.projeto_id == str(projeto_id),
                PosteProjetoORM.codigo == poste_codigo,
            )
        ).one_or_none()