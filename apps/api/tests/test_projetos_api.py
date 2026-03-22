"""Testes de API para intake e workflow de projetos."""

from __future__ import annotations

from fastapi.testclient import TestClient

from apps.api.main import create_app


def build_client() -> TestClient:
    app = create_app("sqlite+pysqlite:///:memory:")
    return TestClient(app)


def payload_projeto() -> dict:
    return {
        "codigo": "ZNA-201",
        "nome": "Projeto API",
        "localidade": "Bangu",
        "checklist_triagem": {
            "tipo_projeto": "Robustez BT",
            "recebeu_leitura_trafo_maxima": True,
            "corrente_trafo_a": 25.5,
            "carga_maxima_transformador_kva": 95.0,
            "possui_fotos_campo": True,
        },
        "evidencias": [
            {
                "tipo": "Foto de Campo",
                "descricao": "Registro fotográfico inicial",
                "caminho_arquivo": "campo/zna-201/01.jpg",
            }
        ],
    }


def test_post_projetos_cria_projeto_com_sucesso() -> None:
    client = build_client()

    response = client.post("/projetos/", json=payload_projeto())

    assert response.status_code == 201
    body = response.json()
    assert body["codigo"] == "ZNA-201"
    assert body["etapa_atual"] == "Triagem"


def test_post_projetos_falha_com_tipo_invalido() -> None:
    client = build_client()
    payload = payload_projeto()
    payload["checklist_triagem"]["tipo_projeto"] = "Tipo Invalido"

    response = client.post("/projetos/", json=payload)

    assert response.status_code == 422


def test_patch_projeto_avanca_etapa_para_cqt() -> None:
    client = build_client()
    criado = client.post("/projetos/", json=payload_projeto())
    projeto_id = criado.json()["id"]

    response = client.patch(
        f"/projetos/{projeto_id}/etapa",
        json={
            "nova_etapa": "CQT",
            "responsavel": "Equipe Engenharia",
            "justificativa": "Triagem concluida com evidencias.",
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["projeto"]["etapa_atual"] == "CQT"
    assert body["historico"]["etapa_destino"] == "CQT"


def test_patch_projeto_falha_quando_tenta_pular_etapa() -> None:
    client = build_client()
    criado = client.post("/projetos/", json=payload_projeto())
    projeto_id = criado.json()["id"]

    response = client.patch(
        f"/projetos/{projeto_id}/etapa",
        json={
            "nova_etapa": "CAD",
            "responsavel": "Equipe Engenharia",
        },
    )

    assert response.status_code == 400
    assert "Transicao invalida" in response.json()["detail"]