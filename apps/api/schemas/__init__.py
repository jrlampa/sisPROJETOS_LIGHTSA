"""DTOs de entrada e saida da API de projetos."""

from .cqt_schemas import (
    CQTAnaliseRequest,
    CQTAnaliseResponse,
    CentroCargaDTO,
    CondutorDTO,
    TipoRedeDTO,
    TransformadorDTO,
    TrechoEletricoDTO,
)
from .projeto_schemas import (
    AvancarEtapaRequest,
    AvancarEtapaResponse,
    ChecklistTriagemDTO,
    EtapaProjetoDTO,
    EvidenciaDTO,
    HistoricoAuditoriaResponse,
    ProjetoCreateRequest,
    ProjetoResponse,
    TipoEvidenciaDTO,
    TipoProjetoDTO,
)

__all__ = [
    "CQTAnaliseRequest",
    "CQTAnaliseResponse",
    "CentroCargaDTO",
    "CondutorDTO",
    "TipoRedeDTO",
    "TransformadorDTO",
    "TrechoEletricoDTO",
    "AvancarEtapaRequest",
    "AvancarEtapaResponse",
    "ChecklistTriagemDTO",
    "EtapaProjetoDTO",
    "EvidenciaDTO",
    "HistoricoAuditoriaResponse",
    "ProjetoCreateRequest",
    "ProjetoResponse",
    "TipoEvidenciaDTO",
    "TipoProjetoDTO",
]
