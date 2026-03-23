"""DTOs de entrada e saida da API de projetos."""

from .cad_schemas import ImportacaoDxfResponse, LayerSumarioDTO
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
from .exportacao_schemas import (
    GerarPacoteResponse,
    PacoteEntregaDTO,
    StatusExportacaoDTO,
)
from .tracao_schemas import (
    CalcularTracaoRequest,
    CalcularTracaoResponse,
    PosteBrutoDTO,
    ResultadoTracaoDTO,
    VaoDTO,
)

__all__ = [
    "ImportacaoDxfResponse",
    "LayerSumarioDTO",
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
    "GerarPacoteResponse",
    "PacoteEntregaDTO",
    "StatusExportacaoDTO",
    "CalcularTracaoRequest",
    "CalcularTracaoResponse",
    "PosteBrutoDTO",
    "ResultadoTracaoDTO",
    "VaoDTO",
]
