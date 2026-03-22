"""Testes unitários das entidades CAD 2.5D da camada de domínio."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from packages.domain.cad.models import ArquivoDXF, GeometriaProjeto, LayerTecnica, Ponto, Segmento


def test_cria_ponto_com_z_padrao_em_2_5d() -> None:
    ponto = Ponto(x=10.0, y=20.0)

    assert ponto.x == 10.0
    assert ponto.y == 20.0
    assert ponto.z == 0.0


def test_segmento_calcula_comprimento_no_plano_xy() -> None:
    segmento = Segmento(
        ponto_inicial=Ponto(x=0.0, y=0.0, z=0.0),
        ponto_final=Ponto(x=3.0, y=4.0, z=10.0),
    )

    assert segmento.comprimento_plano_xy == pytest.approx(5.0)


def test_segmento_falha_quando_pontos_sao_iguais() -> None:
    with pytest.raises(ValidationError, match="ponto inicial e final nao podem ser identicos"):
        Segmento(
            ponto_inicial=Ponto(x=100.0, y=200.0, z=0.0),
            ponto_final=Ponto(x=100.0, y=200.0, z=0.0),
        )


def test_segmento_falha_quando_comprimento_xy_e_zero_mesmo_com_z_diferente() -> None:
    with pytest.raises(ValidationError, match="comprimento no plano XY deve ser maior que zero"):
        Segmento(
            ponto_inicial=Ponto(x=50.0, y=75.0, z=1.0),
            ponto_final=Ponto(x=50.0, y=75.0, z=3.0),
        )


def test_geometria_e_arquivo_dxf_consolidam_segmentos() -> None:
    layer = LayerTecnica(nome="Rede BT", cor_autocad=3)
    segmento_1 = Segmento(
        ponto_inicial=Ponto(x=0.0, y=0.0),
        ponto_final=Ponto(x=6.0, y=8.0),
    )
    segmento_2 = Segmento(
        ponto_inicial=Ponto(x=6.0, y=8.0),
        ponto_final=Ponto(x=9.0, y=12.0),
    )
    geometria = GeometriaProjeto(
        nome="Trecho Piloto",
        layer_tecnica=layer,
        segmentos=(segmento_1, segmento_2),
    )
    arquivo = ArquivoDXF(nome_arquivo="projeto_piloto.dxf", geometrias=(geometria,))

    assert geometria.comprimento_total_xy == pytest.approx(10.0 + 5.0)
    assert arquivo.quantidade_segmentos == 2
