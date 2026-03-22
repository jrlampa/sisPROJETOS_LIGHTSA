"""Testes de API para endpoints do motor CQT."""

from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.main import create_app


def build_client() -> TestClient:
    app = create_app("sqlite+pysqlite:///:memory:")
    return TestClient(app)


def payload_projeto() -> dict:
    return {
        "codigo": "ZNA-CQT-API-001",
        "nome": "Projeto API CQT",
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
                "descricao": "Foto base para analise CQT",
                "caminho_arquivo": "campo/zna-cqt-api-001/01.jpg",
            }
        ],
    }


def payload_cqt_golden_case() -> dict:
    return {
        "tipo_projeto": "Robustez BT",
        "recebeu_leitura_trafo_maxima": True,
        "corrente_trafo_a": 110.0,
        "carga_maxima_transformador_kva": 75.0,
        "centro_carga": {
            "nome": "CC API GOLDEN",
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
                },
                {
                    "nome": "Ramal Final",
                    "tipo_rede": "ramal",
                    "fases": 1,
                    "comprimento_m": 50.0,
                    "corrente_a": 20.0,
                    "tensao_nominal_v": 220.0,
                    "ordem_no_circuito": 2,
                    "consumidores_montante": 15,
                    "consumidores_jusante": 10,
                    "fases_montante": 1,
                    "fases_jusante": 1,
                    "condutor": {
                        "nome": "70 Al - MX",
                        "resistencia_ohm_km": 0.45,
                        "ampacidade_a": 140.0,
                    },
                },
            ],
        },
    }


def test_post_projeto_cqt_retorna_calculos() -> None:
    client = build_client()
    projeto_resp = client.post("/projetos/", json=payload_projeto())
    projeto_id = projeto_resp.json()["id"]

    response = client.post(f"/projetos/{projeto_id}/cqt", json=payload_cqt_golden_case())

    assert response.status_code == 201
    body = response.json()
    assert body["tipo_projeto"] == "Robustez BT"
    assert body["trafo_dentro_do_limite"] is True
    assert body["qdt_total_dentro_do_limite"] is True
    assert body["centro_carga"]["trechos"][0]["queda_tensao_percent"] > 0


def test_post_projeto_cqt_retorna_404_para_projeto_inexistente() -> None:
    client = build_client()
    response = client.post(
        "/projetos/11111111-1111-1111-1111-111111111111/cqt",
        json=payload_cqt_golden_case(),
    )

    assert response.status_code == 404


def test_post_projeto_cqt_retorna_400_quando_payload_invalido() -> None:
    client = build_client()
    projeto_resp = client.post("/projetos/", json=payload_projeto())
    projeto_id = projeto_resp.json()["id"]

    payload = payload_cqt_golden_case()
    payload["centro_carga"]["trechos"][0]["corrente_a"] = 1000.0

    response = client.post(f"/projetos/{projeto_id}/cqt", json=payload)

    assert response.status_code == 400
