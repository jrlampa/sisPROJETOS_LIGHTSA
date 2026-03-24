"""Testes de API para geracao e download do pacote tecnico."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from apps.api.core.security import get_current_user
from apps.api.main import create_app
from packages.domain.auth.models import RoleUsuario, Usuario

_TEST_ADMIN = Usuario(email="test@api.com", nome="Test Admin", role=RoleUsuario.ADMIN)


def build_client() -> TestClient:
    app = create_app("sqlite+pysqlite:///:memory:")
    app.dependency_overrides[get_current_user] = lambda: _TEST_ADMIN
    return TestClient(app)


def payload_projeto() -> dict:
    return {
        "codigo": "ZNA-EXP-API-001",
        "nome": "Projeto API Exportacao",
        "localidade": "Bangu",
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
                "descricao": "Foto base para exportacao",
                "caminho_arquivo": "campo/zna-exp-api-001/01.jpg",
            }
        ],
    }


def payload_cqt() -> dict:
    return {
        "tipo_projeto": "Robustez BT",
        "recebeu_leitura_trafo_maxima": True,
        "corrente_trafo_a": 110.0,
        "carga_maxima_transformador_kva": 75.0,
        "centro_carga": {
            "nome": "CC API EXPORT",
            "transformador": {
                "descricao": "Trafo 112.5kVA",
                "potencia_nominal_kva": 112.5,
                "carga_maxima_lida_kva": 75.0,
                "corrente_lida_a": 110.0,
            },
            "trechos": [
                {
                    "nome": "Trecho Principal",
                    "tipo_rede": "rede",
                    "fases": 3,
                    "comprimento_m": 120.0,
                    "corrente_a": 35.0,
                    "tensao_nominal_v": 13800.0,
                    "ordem_no_circuito": 1,
                    "consumidores_montante": 20,
                    "consumidores_jusante": 15,
                    "fases_montante": 3,
                    "fases_jusante": 3,
                    "condutor": {
                        "nome": "240 Al - Arm",
                        "resistencia_ohm_km": 0.15,
                        "ampacidade_a": 426.0,
                    },
                }
            ],
        },
    }


def payload_tracao() -> dict:
    return {
        "postes": [
            {
                "codigo": "PE-EXP-API-001",
                "resistencia_nominal_daN": 300.0,
                "vaos": [
                    {
                        "comprimento_m": 80.0,
                        "tipo_cabo": "CAA 70mm2",
                        "tracao_daN": 200.0,
                        "azimute_graus": 0.0,
                    }
                ],
            }
        ]
    }


def test_post_gerar_e_get_download_pacote_exportacao() -> None:
    client = build_client()

    projeto_resp = client.post("/api/projetos/", json=payload_projeto())
    assert projeto_resp.status_code == 201
    projeto_id = projeto_resp.json()["id"]

    cqt_resp = client.post(f"/api/projetos/{projeto_id}/cqt", json=payload_cqt())
    assert cqt_resp.status_code == 201

    tracao_resp = client.post(f"/api/projetos/{projeto_id}/tracao", json=payload_tracao())
    assert tracao_resp.status_code == 200

    gerar_resp = client.post(f"/api/projetos/{projeto_id}/exportacao/gerar")
    assert gerar_resp.status_code == 200
    pacote = gerar_resp.json()["pacote"]
    assert pacote["status"] == "CONCLUIDO"

    download_resp = client.get(f"/api/projetos/{projeto_id}/exportacao/download")
    assert download_resp.status_code == 200
    assert download_resp.headers["content-type"].startswith("application/zip")

    caminho_zip = Path(pacote["caminho_arquivo"])
    if caminho_zip.exists():
        for item in caminho_zip.parent.iterdir():
            item.unlink(missing_ok=True)
        caminho_zip.parent.rmdir()
