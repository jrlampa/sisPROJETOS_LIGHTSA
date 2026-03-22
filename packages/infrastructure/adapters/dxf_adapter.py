"""Adaptador de leitura de arquivos DXF usando a biblioteca ezdxf.

Responsabilidade unica: traduzir entidades LINE de um ficheiro DXF fisico
em entidades puras do dominio CAD 2.5D, sem qualquer dependencia de ORM ou API.
"""

from __future__ import annotations

from pathlib import Path

import ezdxf

from packages.domain.cad.models import (
    ArquivoDXF,
    GeometriaProjeto,
    LayerTecnica,
    Ponto,
    Segmento,
)

# Cor AutoCAD padrao (branco) usada quando o DXF nao define cor para a layer.
_COR_AUTOCAD_PADRAO: int = 7

# Comprimento minimo exigido por LayerTecnica.nome (min_length=3).
_NOME_LAYER_MIN_LEN: int = 3


def _normalizar_nome_layer(nome: str) -> str:
    """Garante que o nome da layer satisfaca o min_length=3 do dominio.

    O nome padrao '0' do AutoCAD e nomes muito curtos sao prefixados com
    'DXF_' para distingui-los e satisfazer a restricao de dominio.
    """
    if len(nome) < _NOME_LAYER_MIN_LEN:
        return f"DXF_{nome}"
    return nome


def _cor_da_layer(doc: ezdxf.document.Drawing, nome_layer: str) -> int:
    """Recupera a cor AutoCAD (1-255) da definicao da layer no DXF.

    Falha silenciosa: retorna a cor padrao quando a cor estiver fora do
    intervalo valido (0 = ByBlock, valores negativos = desligada/bloqueada).
    """
    try:
        layer_entry = doc.layers.get(nome_layer)
        if layer_entry is not None:
            cor = layer_entry.dxf.color
            if 1 <= cor <= 255:
                return cor
    except Exception:  # noqa: BLE001
        pass
    return _COR_AUTOCAD_PADRAO


class EzdxfAdapter:
    """Adaptador que converte LINEs de um ficheiro DXF em entidades de dominio.

    Fluxo:
    1. Abre o DXF com ezdxf.readfile.
    2. Itera entidades LINE do modelspace.
    3. Agrupa segmentos pela layer de cada LINE.
    4. Cria GeometriaProjeto por layer com a respectiva LayerTecnica.
    5. Retorna um ArquivoDXF com todas as geometrias agrupadas.

    Segmentos degenerados (comprimento XY == 0) sao silenciosamente ignorados,
    pois sao invalidos para o dominio 2.5D.
    """

    def ler_dxf(self, caminho_arquivo: str) -> ArquivoDXF:
        """Le um ficheiro DXF do disco e retorna as geometrias como ArquivoDXF.

        Args:
            caminho_arquivo: Caminho absoluto ou relativo para o ficheiro .dxf.

        Returns:
            ArquivoDXF com as geometrias agrupadas por layer tecnica.

        Raises:
            FileNotFoundError: Se o ficheiro nao existir.
            ezdxf.DXFError: Se o ficheiro nao for um DXF valido.
        """
        doc = ezdxf.readfile(caminho_arquivo)
        msp = doc.modelspace()

        # Acumula segmentos por nome de layer (nome original, antes da normalizacao)
        segmentos_por_layer: dict[str, list[Segmento]] = {}

        for entidade in msp.query("LINE"):
            nome_layer_original: str = entidade.dxf.layer
            start = entidade.dxf.start
            end = entidade.dxf.end

            ponto_inicial = Ponto(x=float(start.x), y=float(start.y), z=float(start.z))
            ponto_final = Ponto(x=float(end.x), y=float(end.y), z=float(end.z))

            try:
                segmento = Segmento(ponto_inicial=ponto_inicial, ponto_final=ponto_final)
            except ValueError:
                # Ignora segmentos com comprimento XY zero (ex.: linhas verticais puras).
                continue

            segmentos_por_layer.setdefault(nome_layer_original, []).append(segmento)

        geometrias: list[GeometriaProjeto] = []
        for nome_layer_original, segmentos in segmentos_por_layer.items():
            nome_normalizado = _normalizar_nome_layer(nome_layer_original)
            cor = _cor_da_layer(doc, nome_layer_original)

            layer_tecnica = LayerTecnica(nome=nome_normalizado, cor_autocad=cor)
            geometria = GeometriaProjeto(
                nome=nome_normalizado,
                layer_tecnica=layer_tecnica,
                segmentos=tuple(segmentos),
            )
            geometrias.append(geometria)

        nome_arquivo = Path(caminho_arquivo).name
        return ArquivoDXF(
            nome_arquivo=nome_arquivo,
            geometrias=tuple(geometrias),
        )
