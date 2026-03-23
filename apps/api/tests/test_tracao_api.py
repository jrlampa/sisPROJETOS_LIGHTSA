"""Testes de API para endpoint do motor de tracao."""

from __future__ import annotations

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
        "codigo": "ZNA-TRACAO-API-001",
        "nome": "Projeto API Tracao",
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
                "descricao": "Foto base para tracao",
                "caminho_arquivo": "campo/zna-tracao-api-001/01.jpg",
            }
        ],
    }


def payload_tracao() -> dict:
    return {
        "postes": [
            {
                "codigo": "PE-API-001",
                "resistencia_nominal_daN": 300.0,
                "vaos": [
                    {
                        "comprimento_m": 80.0,
                        "tipo_cabo": "CAA 70mm2",
                        "tracao_daN": 200.0,
                        "azimute_graus": 0.0,
                    }
                ],
            },
            {
                "codigo": "PE-API-002",
                "resistencia_nominal_daN": 300.0,
                "vaos": [
                    {
                        "comprimento_m": 90.0,
                        "tipo_cabo": "CAA 70mm2",
                        "tracao_daN": 350.0,
                        "azimute_graus": 0.0,
                    }
                ],
            },
        ]
    }


def test_post_projeto_tracao_retorna_estados_mecanicos_corretos() -> None:
    client = build_client()

    projeto_resp = client.post("/projetos/", json=payload_projeto())
    assert projeto_resp.status_code == 201
    projeto_id = projeto_resp.json()["id"]

    response = client.post(f"/projetos/{projeto_id}/tracao", json=payload_tracao())

    assert response.status_code == 200
    body = response.json()

    assert len(body["resultados"]) == 2
    assert body["resultados"][0]["estado_mecanico"] == "APROVADO"
    assert body["resultados"][1]["estado_mecanico"] == "REPROVADO"
