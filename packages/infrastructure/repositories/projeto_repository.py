"""Repositorio de projetos e auditoria para persistencia SQLite local-first."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from packages.domain.intake.models import ChecklistTriagem, Evidencia, Projeto
from packages.domain.workflow.models import EtapaProjeto, HistoricoAuditoria
from packages.infrastructure.database.models import HistoricoAuditoriaORM, ProjetoORM


class ProjetoRepository:
    """Traduz entidades de dominio para ORM sem vazar SQLAlchemy para o dominio."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def salvar_projeto(self, projeto: Projeto) -> Projeto:
        registro = ProjetoORM(
            id=str(projeto.id),
            codigo=projeto.codigo,
            nome=projeto.nome,
            localidade=projeto.localidade,
            etapa_atual=projeto.etapa_atual.value,
            checklist_triagem=projeto.checklist_triagem.model_dump(mode="json"),
            evidencias=[evidencia.model_dump(mode="json") for evidencia in projeto.evidencias],
            criado_em=projeto.criado_em,
        )
        self._session.add(registro)
        return projeto

    def buscar_projeto_por_id(self, projeto_id: UUID) -> Projeto | None:
        registro = self._session.get(ProjetoORM, str(projeto_id))
        if registro is None:
            return None
        return self._to_domain(registro)

    def atualizar_projeto(self, projeto: Projeto) -> Projeto:
        registro = self._session.get(ProjetoORM, str(projeto.id))
        if registro is None:
            raise ValueError("Projeto nao encontrado para atualizacao.")

        registro.codigo = projeto.codigo
        registro.nome = projeto.nome
        registro.localidade = projeto.localidade
        registro.etapa_atual = projeto.etapa_atual.value
        registro.checklist_triagem = projeto.checklist_triagem.model_dump(mode="json")
        registro.evidencias = [
            evidencia.model_dump(mode="json") for evidencia in projeto.evidencias
        ]
        registro.criado_em = projeto.criado_em
        return projeto

    def registrar_historico_auditoria(self, historico: HistoricoAuditoria) -> HistoricoAuditoria:
        registro = HistoricoAuditoriaORM(
            id=str(historico.id),
            projeto_id=str(historico.projeto_id),
            etapa_origem=historico.etapa_origem.value if historico.etapa_origem else None,
            etapa_destino=historico.etapa_destino.value,
            acao=historico.acao,
            responsavel=historico.responsavel,
            justificativa=historico.justificativa,
            ocorrido_em=historico.ocorrido_em,
        )
        self._session.add(registro)
        return historico

    @staticmethod
    def _to_domain(registro: ProjetoORM) -> Projeto:
        checklist = ChecklistTriagem.model_validate(registro.checklist_triagem)
        evidencias = tuple(Evidencia.model_validate(item) for item in registro.evidencias)
        return Projeto(
            id=UUID(registro.id),
            codigo=registro.codigo,
            nome=registro.nome,
            localidade=registro.localidade,
            etapa_atual=EtapaProjeto(registro.etapa_atual),
            checklist_triagem=checklist,
            evidencias=evidencias,
            criado_em=registro.criado_em,
        )
