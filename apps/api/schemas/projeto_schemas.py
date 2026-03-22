"""DTOs versionados para contratos de API de intake e workflow."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from packages.domain.intake.models import Projeto
from packages.domain.workflow.models import HistoricoAuditoria


class TipoProjetoDTO(str, Enum):
    """Tipos de projeto aceitos pelo contrato da API."""

    LIGACAO_NOVA = "Ligacao Nova"
    ROBUSTEZ_MT = "Robustez MT"
    ROBUSTEZ_BT = "Robustez BT"
    CLANDESTINOS = "Clandestinos"
    RECONDUTORAMENTO = "Recondutoramento"
    EXTENSAO_REDE = "Extensao de Rede"
    SUBDIVISAO_CIRCUITO = "Subdivisao de Circuito"


class TipoEvidenciaDTO(str, Enum):
    """Classificacao de evidencias no contrato da API."""

    FOTO_CAMPO = "Foto de Campo"
    STREET_VIEW = "Street View"
    DESENHO_REFERENCIA = "Desenho de Referencia"
    LEVANTAMENTO = "Levantamento"
    DOCUMENTO = "Documento"
    OUTRO = "Outro"


class EtapaProjetoDTO(str, Enum):
    """Etapas de workflow expostas no contrato da API."""

    TRIAGEM = "Triagem"
    CQT = "CQT"
    CAD = "CAD"
    TRACAO = "Tracao"
    EXPORTACAO = "Exportacao"


class EvidenciaDTO(BaseModel):
    """DTO de evidencia para entrada e saida da API."""

    model_config = ConfigDict(extra="forbid")

    id: UUID | None = None
    tipo: TipoEvidenciaDTO
    descricao: str = Field(min_length=3, max_length=500)
    caminho_arquivo: str | None = Field(default=None, min_length=3, max_length=500)
    url: HttpUrl | None = None
    coletado_em: datetime | None = None


class ChecklistTriagemDTO(BaseModel):
    """DTO de checklist de triagem para payloads de intake."""

    model_config = ConfigDict(extra="forbid")

    tipo_projeto: TipoProjetoDTO
    recebeu_leitura_trafo_maxima: bool = False
    corrente_trafo_a: float | None = Field(default=None, gt=0)
    carga_maxima_transformador_kva: float | None = Field(default=None, gt=0)
    possui_fotos_campo: bool = False
    comparou_com_street_view: bool = False
    comparou_com_desenho_recebido: bool = False
    recuperacao_clandestino_confirmada: bool | None = None
    quantidade_ligacoes_irregulares: int | None = Field(default=None, ge=1)
    observacoes: str | None = Field(default=None, max_length=1000)


class ProjetoCreateRequest(BaseModel):
    """Payload de entrada para criacao de projeto."""

    model_config = ConfigDict(extra="forbid")

    codigo: str = Field(min_length=3, max_length=100)
    nome: str = Field(min_length=3, max_length=200)
    localidade: str = Field(min_length=3, max_length=200)
    checklist_triagem: ChecklistTriagemDTO
    evidencias: list[EvidenciaDTO] = Field(default_factory=list)


class ProjetoResponse(BaseModel):
    """Resposta padrao de projeto no contrato v1 da API."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    codigo: str
    nome: str
    localidade: str
    etapa_atual: EtapaProjetoDTO
    checklist_triagem: ChecklistTriagemDTO
    evidencias: list[EvidenciaDTO]
    criado_em: datetime

    @classmethod
    def from_domain(cls, projeto: Projeto) -> "ProjetoResponse":
        return cls.model_validate(
            {
                "id": projeto.id,
                "codigo": projeto.codigo,
                "nome": projeto.nome,
                "localidade": projeto.localidade,
                "etapa_atual": projeto.etapa_atual.value,
                "checklist_triagem": projeto.checklist_triagem.model_dump(mode="json"),
                "evidencias": [item.model_dump(mode="json") for item in projeto.evidencias],
                "criado_em": projeto.criado_em,
            }
        )


class AvancarEtapaRequest(BaseModel):
    """Payload de entrada para avancar etapa do projeto."""

    model_config = ConfigDict(extra="forbid")

    nova_etapa: EtapaProjetoDTO
    responsavel: str = Field(min_length=3, max_length=120)
    justificativa: str | None = Field(default=None, max_length=1000)


class HistoricoAuditoriaResponse(BaseModel):
    """Resposta de auditoria no contrato de workflow."""

    model_config = ConfigDict(extra="forbid")

    id: UUID
    projeto_id: UUID
    etapa_origem: EtapaProjetoDTO | None = None
    etapa_destino: EtapaProjetoDTO
    acao: str
    responsavel: str
    justificativa: str | None = None
    ocorrido_em: datetime

    @classmethod
    def from_domain(cls, historico: HistoricoAuditoria) -> "HistoricoAuditoriaResponse":
        return cls.model_validate(
            {
                "id": historico.id,
                "projeto_id": historico.projeto_id,
                "etapa_origem": historico.etapa_origem.value if historico.etapa_origem else None,
                "etapa_destino": historico.etapa_destino.value,
                "acao": historico.acao,
                "responsavel": historico.responsavel,
                "justificativa": historico.justificativa,
                "ocorrido_em": historico.ocorrido_em,
            }
        )


class AvancarEtapaResponse(BaseModel):
    """Resposta combinada de projeto atualizado e evento de auditoria."""

    model_config = ConfigDict(extra="forbid")

    projeto: ProjetoResponse
    historico: HistoricoAuditoriaResponse
