"""Casos de uso de intake e workflow do projeto."""

from __future__ import annotations

from collections.abc import Callable
from uuid import UUID

from sqlalchemy.orm import Session

from packages.domain.intake.models import Projeto
from packages.domain.workflow.models import EtapaProjeto, HistoricoAuditoria
from packages.infrastructure.repositories.projeto_repository import ProjetoRepository

TRANSICOES_VALIDAS: dict[EtapaProjeto, set[EtapaProjeto]] = {
    EtapaProjeto.TRIAGEM: {EtapaProjeto.CQT},
    EtapaProjeto.CQT: {EtapaProjeto.CAD},
    EtapaProjeto.CAD: {EtapaProjeto.TRACAO},
    EtapaProjeto.TRACAO: {EtapaProjeto.EXPORTACAO},
    EtapaProjeto.EXPORTACAO: set(),
}


class CriarProjetoUseCase:
    """Valida dados brutos de entrada e persiste um projeto no repositório.

    O caso de uso protege o domínio contra payloads inválidos e centraliza o fluxo
    de criação para a camada de aplicação.
    """

    def __init__(
        self,
        session_factory: Callable[[], Session],
        repository: ProjetoRepository | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._repository = repository

    def executar(self, dados_brutos: dict) -> Projeto:
        projeto = Projeto.model_validate(dados_brutos)
        with self._session_factory() as session:
            repository = self._repository or ProjetoRepository(session)
            projeto_salvo = repository.salvar_projeto(projeto)
            session.commit()
            return projeto_salvo


class AvancarEtapaUseCase:
    """Avança o projeto para a próxima etapa válida e registra auditoria.

    A regra de governança permite apenas a sequência linear definida no fluxo
    operacional da LIGHT: Triagem -> CQT -> CAD -> Tracao -> Exportacao.
    """

    def __init__(
        self,
        session_factory: Callable[[], Session],
        repository: ProjetoRepository | None = None,
    ) -> None:
        self._session_factory = session_factory
        self._repository = repository

    def executar(
        self,
        *,
        projeto_id: UUID,
        nova_etapa: EtapaProjeto,
        responsavel: str,
        justificativa: str | None = None,
    ) -> tuple[Projeto, HistoricoAuditoria]:
        with self._session_factory() as session:
            repository = self._repository or ProjetoRepository(session)
            projeto = repository.buscar_projeto_por_id(projeto_id)
            if projeto is None:
                raise ValueError("Projeto nao encontrado para avancar etapa.")

            etapas_permitidas = TRANSICOES_VALIDAS[projeto.etapa_atual]
            if nova_etapa not in etapas_permitidas:
                raise ValueError(
                    f"Transicao invalida de {projeto.etapa_atual.value} para {nova_etapa.value}."
                )

            projeto_atualizado = projeto.model_copy(update={"etapa_atual": nova_etapa})
            historico = HistoricoAuditoria(
                projeto_id=projeto.id,
                etapa_origem=projeto.etapa_atual,
                etapa_destino=nova_etapa,
                acao=f"Avanco da etapa {projeto.etapa_atual.value} para {nova_etapa.value}",
                responsavel=responsavel,
                justificativa=justificativa,
            )

            repository.atualizar_projeto(projeto_atualizado)
            repository.registrar_historico_auditoria(historico)
            session.commit()
            return projeto_atualizado, historico
