"""Testes de caos para hardening da API contra entradas imprevisiveis."""

from __future__ import annotations

import io

import pytest
from fastapi.testclient import TestClient

from apps.api.core.security import create_access_token, get_current_user
from apps.api.main import create_app
from packages.domain.auth.models import RoleUsuario, Usuario

_TEST_ADMIN = Usuario(email="test@api.com", nome="Test Admin", role=RoleUsuario.ADMIN)


def build_client_admin() -> TestClient:
    app = create_app("sqlite+pysqlite:///:memory:")
    app.dependency_overrides[get_current_user] = lambda: _TEST_ADMIN
    return TestClient(app)


def build_client_sem_override() -> TestClient:
    app = create_app("sqlite+pysqlite:///:memory:")
    return TestClient(app)


def payload_projeto(codigo: str = "ZNA-CHAOS-001") -> dict:
    return {
        "codigo": codigo,
        "nome": "Projeto Chaos",
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
                "descricao": "Base Chaos",
                "caminho_arquivo": "campo/zna-chaos-001/01.jpg",
            }
        ],
    }


def payload_cqt_valido() -> dict:
    return {
        "tipo_projeto": "Robustez BT",
        "recebeu_leitura_trafo_maxima": True,
        "corrente_trafo_a": 110.0,
        "carga_maxima_transformador_kva": 75.0,
        "centro_carga": {
            "nome": "CC CHAOS",
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


def test_chaos_cqt_rejeita_strings_no_lugar_de_numeros() -> None:
    client = build_client_admin()
    projeto_resp = client.post("/projetos/", json=payload_projeto())
    assert projeto_resp.status_code == 201
    projeto_id = projeto_resp.json()["id"]

    payload = payload_cqt_valido()
    payload["corrente_trafo_a"] = "lixo"
    payload["centro_carga"]["trechos"][0]["comprimento_m"] = "abc"

    response = client.post(f"/projetos/{projeto_id}/cqt", json=payload)

    assert response.status_code == 422
    assert "Dados invalidos" in response.json()["detail"]


def test_chaos_dxf_txt_disfarcado_retorna_422_com_mensagem_clara() -> None:
    client = build_client_admin()
    projeto_resp = client.post("/projetos/", json=payload_projeto("ZNA-CHAOS-002"))
    assert projeto_resp.status_code == 201
    projeto_id = projeto_resp.json()["id"]

    fake_file = io.BytesIO(b"isto nao e um ficheiro dxf valido")
    response = client.post(
        f"/projetos/{projeto_id}/dxf",
        files={"file": ("malicioso.txt", fake_file, "text/plain")},
    )

    assert response.status_code == 422
    assert response.json()["detail"] == "Formato de ficheiro invalido. Envie um DXF valido."


@pytest.mark.parametrize(
    "token",
    [
        "token-malformado",
        create_access_token("expired@test.com", RoleUsuario.ADMIN, expires_minutes=-1),
    ],
)
def test_chaos_jwt_malformado_ou_expirado_retorna_401(token: str) -> None:
    client = build_client_sem_override()

    response = client.post(
        "/projetos/",
        headers={"Authorization": f"Bearer {token}"},
        json=payload_projeto("ZNA-CHAOS-003"),
    )

    assert response.status_code == 401
    assert "Token de autenticacao invalido ou expirado." in response.json()["detail"]
