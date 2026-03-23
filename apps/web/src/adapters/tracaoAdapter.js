const CAMPOS_COM_DADOS = ["tipoCabo", "vao", "flecha", "angulo", "qtdCabos", "qtdLigacoes"];

export function toNumberOr(defaultValue, value) {
  const number = Number(value);
  return Number.isFinite(number) ? number : defaultValue;
}

function temDadosTravessia(travessia) {
  return CAMPOS_COM_DADOS.some((key) => String(travessia[key] || "").trim() !== "");
}

export function secaoToPayload(sectionKey, travessias, resistenciaNominal) {
  return travessias
    .map((travessia, idx) => ({ travessia, idx }))
    .filter(({ travessia }) => temDadosTravessia(travessia))
    .map(({ travessia, idx }) => ({
      codigo: `${sectionKey.toUpperCase()}-T${idx + 1}`,
      resistencia_nominal_daN: resistenciaNominal,
      vaos: [
        {
          comprimento_m: toNumberOr(10, travessia.vao),
          tipo_cabo: travessia.tipoCabo || "CAA 70mm2",
          tracao_daN: toNumberOr(100, travessia.flecha || travessia.qtdCabos || travessia.qtdLigacoes),
          azimute_graus: toNumberOr(0, travessia.angulo) % 360,
        },
      ],
    }));
}

export function mapResultadosPorSecao(indexMap, resultados) {
  const bySection = {
    mt1: ["-", "-", "-", "-"],
    mt2: ["-", "-", "-", "-"],
    bt: ["-", "-", "-", "-"],
    ral: ["-", "-", "-", "-"],
  };

  resultados.forEach((res, i) => {
    const pos = indexMap[i];
    if (!pos) return;
    bySection[pos.secao][pos.idx] = res.estado_mecanico;
  });

  return bySection;
}

export function montarPostesTracao(secoes, resistenciaNominal) {
  return [
    ...secaoToPayload("mt1", secoes.mt1, resistenciaNominal),
    ...secaoToPayload("mt2", secoes.mt2, resistenciaNominal),
    ...secaoToPayload("bt", secoes.bt, resistenciaNominal),
    ...secaoToPayload("ral", secoes.ral, resistenciaNominal),
  ];
}

export function montarIndexMapTracao(secoes, postosEntrada) {
  const indexMap = [];
  let k = 0;

  ["mt1", "mt2", "bt", "ral"].forEach((secao) => {
    secoes[secao].forEach((travessia, idx) => {
      if (temDadosTravessia(travessia) && postosEntrada[k]) {
        indexMap.push({ secao, idx });
        k += 1;
      }
    });
  });

  return indexMap;
}

export function resumirResultadosTracao(resultados = []) {
  const totais = { APROVADO: 0, ALERTA: 0, REPROVADO: 0 };
  resultados.forEach((item) => {
    const key = item.estado_mecanico;
    if (totais[key] !== undefined) totais[key] += 1;
  });
  return totais;
}
