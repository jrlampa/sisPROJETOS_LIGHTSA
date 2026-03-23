"""Testes de API para o endpoint de upload de ficheiro DXF (motor CAD)."""

from __future__ import annotations

import os
import tempfile

import ezdxf
from fastapi.testclient import TestClient

from apps.api.core.security import get_current_user
from apps.api.main import create_app
from packages.domain.auth.models import RoleUsuario, Usuario

# ---------------------------------------------------------------------------
# Helpers de fixture
# ---------------------------------------------------------------------------

_TEST_ADMIN = Usuario(email="test@api.com", nome="Test Admin", role=RoleUsuario.ADMIN)


def build_client() -> TestClient:
    """Cria TestClient com base de dados SQLite em memória isolada."""
    app = create_app("sqlite+pysqlite:///:memory:")
    app.dependency_overrides[get_current_user] = lambda: _TEST_ADMIN
    return TestClient(app)


def payload_projeto(codigo: str = "ZNA-CAD-API-001") -> dict:
    return {
        "codigo": codigo,
        "nome": "Projeto API CAD",
        "localidade": "Santa Cruz",
        "checklist_triagem": {
            "tipo_projeto": "Robustez BT",
            "recebeu_leitura_trafo_maxima": True,
            "corrente_trafo_a": 30.0,
            "carga_maxima_transformador_kva": 95.0,
            "possui_fotos_campo": True,
        },
        "evidencias": [
            {
                "tipo": "Foto de Campo",
                "descricao": "Foto base CAD",
                "caminho_arquivo": "campo/zna-cad-api-001/01.jpg",
            }
        ],
    }


def criar_dxf_em_disco(linhas: list[tuple], layers: list[dict] | None = None) -> str:
    """Cria um DXF temporário no disco e retorna o caminho.

    Args:
        linhas: lista de (layer, start, end) ou (start, end) se sem layer.
        layers: lista de dicts com {nome, cor} para definir layers no DXF.
    """
    doc = ezdxf.new(dxfversion="R2018")
    msp = doc.modelspace()

    if layers:
        for layer_def in layers:
            doc.layers.add(layer_def["nome"], color=layer_def["cor"])

    for item in linhas:
        if len(item) == 3:
            layer_nome, start, end = item
            msp.add_line(start, end, dxfattribs={"layer": layer_nome})
        else:
            start, end = item
            msp.add_line(start, end)

    with tempfile.NamedTemporaryFile(suffix=".dxf", delete=False, mode="w") as f:
        tmp_path = f.name
    doc.saveas(tmp_path)
    return tmp_path


# ---------------------------------------------------------------------------
# Testes
# ---------------------------------------------------------------------------


def test_upload_dxf_retorna_200_e_sumario_correto():
    """Upload de DXF com 2 segmentos deve retornar HTTP 200 e sumário correto."""
    client = build_client()

    # Cria o projeto
    resp = client.post("/projetos/", json=payload_projeto())
    assert resp.status_code == 201, resp.text
    projeto_id = resp.json()["id"]

    tmp_path = criar_dxf_em_disco(
        [
            ((0.0, 0.0, 0.0), (3.0, 4.0, 0.0)),  # comprimento XY = 5.0
            ((10.0, 0.0, 0.0), (10.0, 10.0, 0.0)),  # comprimento XY = 10.0
        ]
    )

    try:
        with open(tmp_path, "rb") as f:
            resp = client.post(
                f"/projetos/{projeto_id}/dxf",
                files={"file": ("test.dxf", f, "application/octet-stream")},
            )
    finally:
        os.unlink(tmp_path)

    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["nome_arquivo"] == "test.dxf"
    assert body["total_segmentos"] == 2
    # Ambos os segmentos estão na layer default '0' (normalizada para 'DXF_0')
    assert body["total_layers"] == 1
    assert body["layers"][0]["nome"] == "DXF_0"
    assert body["layers"][0]["total_segmentos"] == 2
    # Comprimento total: 5.0 + 10.0 = 15.0
    assert abs(body["layers"][0]["comprimento_total_xy"] - 15.0) < 1e-6


def test_upload_dxf_agrupa_layers_distintas():
    """Segmentos em layers distintas devem aparecer separados no sumário."""
    client = build_client()

    resp = client.post("/projetos/", json=payload_projeto("ZNA-CAD-API-002"))
    assert resp.status_code == 201, resp.text
    projeto_id = resp.json()["id"]

    tmp_path = criar_dxf_em_disco(
        linhas=[
            ("BT_REDE", (0, 0), (5, 0)),
            ("BT_REDE", (0, 0), (0, 5)),
            ("BT_RAMAL", (10, 0), (15, 0)),
        ],
        layers=[{"nome": "BT_REDE", "cor": 1}, {"nome": "BT_RAMAL", "cor": 2}],
    )

    try:
        with open(tmp_path, "rb") as f:
            resp = client.post(
                f"/projetos/{projeto_id}/dxf",
                files={"file": ("projeto.dxf", f, "application/octet-stream")},
            )
    finally:
        os.unlink(tmp_path)

    assert resp.status_code == 200, resp.text
    body = resp.json()

    assert body["total_layers"] == 2
    assert body["total_segmentos"] == 3

    nomes = {layer["nome"] for layer in body["layers"]}
    assert "BT_REDE" in nomes
    assert "BT_RAMAL" in nomes

    contagem = {layer["nome"]: layer["total_segmentos"] for layer in body["layers"]}
    assert contagem["BT_REDE"] == 2
    assert contagem["BT_RAMAL"] == 1


def test_upload_dxf_retorna_404_para_projeto_inexistente():
    """Upload para projeto_id inexistente deve retornar HTTP 404."""
    import uuid

    client = build_client()

    tmp_path = criar_dxf_em_disco([((0, 0, 0), (1, 1, 0))])
    try:
        with open(tmp_path, "rb") as f:
            resp = client.post(
                f"/projetos/{uuid.uuid4()}/dxf",
                files={"file": ("nao_existe.dxf", f, "application/octet-stream")},
            )
    finally:
        os.unlink(tmp_path)

    assert resp.status_code == 404, resp.text
