"""Repositorio de persistencia da analise CQT vinculada ao projeto."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from packages.domain.cqt.models import CQTAnalise
from packages.infrastructure.database.models import (
    CentroCargaORM,
    CondutorORM,
    CQTAnaliseORM,
    PosteProjetoORM,
    ProjetoORM,
    TransformadorORM,
    TrechoEletricoORM,
)
from packages.infrastructure.repositories.base_repository import BaseRepository
from packages.infrastructure.repositories.poste_repository import PosteRepository


class CQTRepositoryultado de CQT sem vazar ORM para a camada de dominio."""

    def __init__(self, session: Session) -> None:
        super().__init__(session)
        s
    def salvar_analise_cqt(self, projeto_id: UUID, analise: CQTAnalise) -> CQTAnalise:
        self._get_projeto_orm(projeto_id, "Projeto nao encontrado para vincular analise CQT.")
=ne.
            tipo_projeto=analise.tipo_projeto.value,
            recuperacao_clandestino_confirmada=analise.recuperacao_clandestino_confirmada,
            quantidade_ligacoes_irregulares=analise.quantidade_ligacoes_irregulares,
            recebeu_leitura_trafo_maxima=analise.recebeu_leitura_trafo_maxima,
            corrente_trafo_a=analise.corrente_trafo_a,
            carga_maxima_transformador_kva=analise.carga_maxima_transformador_kva,
            limite_carregamento_trafo_percent=analise.limite_carregamento_trafo_percent,
            trafo_dentro_do_limite=analise.trafo_dentro_do_limite,
            qdt_total_dentro_do_limite=analise.qdt_total_dentro_do_limite,
            criado_em=analise.criado_em,
        )

        centro = analise.centro_carga
        centro_orm = CentroCargaORM(
            id=str(centro.id),
            nome=centro.nome,
            queda_total_percent=centro.queda_total_percent,
            possui_erro_02=centro.possui_erro_02,
        )

        transformador = centro.transformador
        transformador_orm = TransformadorORM(
            id=str(transformador.id),
            descricao=transformador.descricao,
            potencia_nominal_kva=transformador.potencia_nominal_kva,
            carga_maxima_lida_kva=transformador.carga_maxima_lida_kva,
            corrente_lida_a=transformador.corrente_lida_a,
            fator_carga_percent=transformador.fator_carga_percent,
        )
        centro_orm.transformador = transformador_orm

        # Cache local para otimização do ORM: evita a criação de registros duplicados
        # na tabela de condutores quando o mesmo condutor se repete na análise
        condutores_cache: dict[str, CondutorORM] = {}
        postes_cache: dict[str, PosteProjetoORM] = {}

        for trecho in centro.trechos:
            condutor_key = f"{trecho.condutor.nome}_{trecho.condutor.resistencia_ohm_km}"
            if condutor_key in condutores_cache:
                condutor_orm = condutores_cache[condutor_key]
            else:
                condutor_orm = CondutorORM(
                    nome=trecho.condutor.nome,
                    resistencia_ohm_km=trecho.condutor.resistencia_ohm_km,
                    ampacidade_a=trecho.condutor.ampacidade_a,
                )
                condutores_cache[condutor_key] = condutor_orm

            # Busca ou cria os postes de início e fim do trecho
            poste_de_orm = self._poste_repository.get_or_create_stub(
                projeto_id, trecho.poste_de_codigo, postes_cache
            )
            poste_para_orm = self._poste_repository.get_or_create_stub(
                projeto_id, trecho.poste_para_codigo, postes_cache
            )

            trecho_orm = TrechoEletricoORM(
                id=str(trecho.id),
                # O `nome` agora é uma propriedade computada no domínio
                poste_de_id=poste_de_orm.id,
                poste_para_id=poste_para_orm.id,
                tipo_rede=trecho.tipo_rede.value,
                fases=trecho.fases,
                comprimento_m=trecho.comprimento_m,
                corrente_a=trecho.corrente_a,
                tensao_nominal_v=trecho.tensao_nominal_v,
                ordem_no_circuito=trecho.ordem_no_circuito,
                consumidores_montante=trecho.consumidores_montante,
                consumidores_jusante=trecho.consumidores_jusante,
                fases_montante=trecho.fases_montante,
                fases_jusante=trecho.fases_jusante,
                resistencia_total_ohm=trecho.resistencia_total_ohm,
                queda_tensao_v=trecho.queda_tensao_v,
                queda_tensao_percent=trecho.queda_tensao_percent,
                limite_qdt_percent=trecho.limite_qdt_percent,
                dentro_do_limite_qdt=trecho.dentro_do_limite_qdt,
                possui_erro_02=trecho.possui_erro_02,
            )
            trecho_orm.condutor = condutor_orm
            centro_orm.trechos.append(trecho_orm)

        analise_orm.centro_carga = centro_orm
        self._session.add(analise_orm)
        return analise

    def obter_resumo_por_projeto(self, projeto_id: UUID) -> dict | None:
        """Retorna um resumo da ultima analise CQT para exportacao de ficheiros."""
        analise = self._session.scalars(
            select(CQTAnaliseORM)
            .where(CQTAnaliseORM.projeto_id == str(projeto_id))
            .order_by(CQTAnaliseORM.criado_em.desc())
            .limit(1)
        ).one_or_none()
        if analise is None:
            return None

        return {
            "analise_id": analise.id,
            "tipo_projeto": analise.tipo_projeto,
            "qdt_total_dentro_do_limite": analise.qdt_total_dentro_do_limite,
            "trafo_dentro_do_limite": analise.trafo_dentro_do_limite,
        }
