"""Testes de integracao do caso de uso de importacao de ficheiro DXF."""

from __future__ import annotations

import os
import tempfile
from uuid import UUID

import ezdxf
import pytest

from packages.application.use_cases.cad_use_cases import ImportarArquivoDxfUseCase
from packages.application.use_cases.projeto_use_cases import CriarProjetoUseCase
from packages.infrastructure.database.models import Base, GeometriaProjetoORM
from packages.infrastructure.database.session import build_engine, create_session_factory


# ---------------------------------------------------------------------------
# Helpers de infraestrutura de teste
# ---------------------------------------------------------------------------


def _setup_in_memory_session_factory():
    """Cria engine SQLite em memoria compartilhada e inicializa o schema completo."""
    engine = build_engine("sqlite+pysqlite:///:memory:")
    Base.metadata.create_all(engine)
    return create_session_factory("sqlite+pysqlite:///:memory:", engine=engine)


def _dados_projeto() -> dict:
    return {
        "codigo": "ZNA-CAD-001",
        "nome": "Projeto para CAD",
        "localidade": "Campo Grande",
        "checklist_triagem": {
            "tipo_projeto": "Robustez BT",
            "recebeu_leitura_trafo_maxima": True,
            "corrente_trafo_a": 110.0,
            "carga_maxima_transformador_kva": 75.0,
            "possui_fotos_campo": True,
        },
        "evidencias": [
            {
                "tipo": "Foto de Campo",
                "descricao": "Foto inicial",
                "caminho_arquivo": "campo/projeto-cad-001.jpg",
            }
        ],
    }


def _criar_dxf_temporario(linhas: list[tuple]) -> str:
    """Cria um ficheiro DXF temporario contendo as linhas fornecidas.

    Args:
        linhas: Lista de tuplas ((x1, y1, z1), (x2, y2, z2)) para cada LINE.

    Returns:
        Caminho absoluto do ficheiro DXF criado.
    """
    doc = ezdxf.new(dxfversion="R2018")
    msp = doc.modelspace()
    for start, end in linhas:
        msp.add_line(start, end)

    # Cria ficheiro temporario que persiste apos o with-block (delete=False)
    with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False, mode="w") as f:
        tmp_path = f.name

    doc.saveas(tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------


def test_importar_dxf_persiste_geometria_no_banco():
    """Caso basico: importa um DXF com dois segmentos e valida a persistencia."""
    session_factory = _setup_in_memory_session_factory()

    # Cria o projeto pai
    projeto = CriarProjetoUseCase(session_factory).executar(_dados_projeto())
    projeto_id: UUID = projeto.id

    # Cria DXF temporario com dois segmentos (triangulo 3-4-5 e segmento reto)
    tmp_path = _criar_dxf_temporario([
        ((0.0, 0.0, 0.0), (3.0, 4.0, 0.0)),   # comprimento XY = 5.0
        ((10.0, 0.0, 0.0), (10.0, 10.0, 0.0)), # comprimento XY = 10.0
    ])

    try:
        use_case = ImportarArquivoDxfUseCase(session_factory)
        resultado = use_case.executar(projeto_id, tmp_path)

        # Dominio: ArquivoDXF retornado deve consolidar os 2 segmentos
        assert resultado.quantidade_segmentos == 2

        # Banco: deve existir exatamente um registro vinculado ao projeto
        with session_factory() as session:
            orm = session.query(GeometriaProjetoORM).filter_by(
                projeto_id=str(projeto_id)
            ).one_or_none()

            assert orm is not None, "GeometriaProjetoORM nao foi persistida."
            assert orm.nome_arquivo.endswith(".dxf")
            assert isinstance(orm.dados_geometria, list)
            # A layer default do ezdxf e '0', que e normalizada para 'DXF_0'
            total_segmentos = sum(
                len(geom["segmentos"]) for geom in orm.dados_geometria
            )
            assert total_segmentos == 2
    finally:
        os.unlink(tmp_path)


def test_importar_dxf_agrupa_segmentos_por_layer():
    """Segmentos em layers diferentes devem gerar GeometriaProjeto distintas."""
    session_factory = _setup_in_memory_session_factory()

    projeto = CriarProjetoUseCase(session_factory).executar(
        {**_dados_projeto(), "codigo": "ZNA-CAD-002"}
    )

    doc = ezdxf.new(dxfversion="R2018")
    msp = doc.modelspace()
    # Adiciona layers com nomes validos (min 3 chars)
    doc.layers.add("BT_REDE", color=1)
    doc.layers.add("BT_RAMAL", color=2)

    msp.add_line((0, 0), (5, 0), dxfattribs={"layer": "BT_REDE"})
    msp.add_line((0, 0), (0, 5), dxfattribs={"layer": "BT_REDE"})
    msp.add_line((10, 0), (15, 0), dxfattribs={"layer": "BT_RAMAL"})

    with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False, mode="w") as f:
        tmp_path = f.name
    doc.saveas(tmp_path)

    try:
        use_case = ImportarArquivoDxfUseCase(session_factory)
        resultado = use_case.executar(projeto.id, tmp_path)

        # Duas layers -> duas GeometriaProjeto distintas
        assert len(resultado.geometrias) == 2
        nomes_layers = {g.layer_tecnica.nome for g in resultado.geometrias}
        assert "BT_REDE" in nomes_layers
        assert "BT_RAMAL" in nomes_layers

        # BT_REDE tem 2 segmentos, BT_RAMAL tem 1
        contagem = {g.layer_tecnica.nome: len(g.segmentos) for g in resultado.geometrias}
        assert contagem["BT_REDE"] == 2
        assert contagem["BT_RAMAL"] == 1
    finally:
        os.unlink(tmp_path)


def test_importar_dxf_falha_para_projeto_inexistente():
    """O repositorio deve lancar ValueError para projeto_id invalido."""
    session_factory = _setup_in_memory_session_factory()

    from uuid import uuid4
    projeto_id_inexistente = uuid4()

    tmp_path = _criar_dxf_temporario([((0, 0, 0), (1, 1, 0))])
    try:
        with pytest.raises(ValueError, match="Projeto nao encontrado"):
            ImportarArquivoDxfUseCase(session_factory).executar(
                projeto_id_inexistente, tmp_path
            )
    finally:
        os.unlink(tmp_path)
