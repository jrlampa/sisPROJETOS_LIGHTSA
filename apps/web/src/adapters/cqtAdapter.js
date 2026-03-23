export function obterCondutor(tipoCabo) {
  const nome = (tipoCabo || "").trim();
  if (nome.includes("240")) {
    return { nome, resistencia_ohm_km: 0.15, ampacidade_a: 426 };
  }
  if (nome.includes("70")) {
    return { nome, resistencia_ohm_km: 0.45, ampacidade_a: 140 };
  }
  return { nome: nome || "Condutor Padrao", resistencia_ohm_km: 0.45, ampacidade_a: 140 };
}

export function montarTrechosCqt(linhasTrecho) {
  return linhasTrecho.map((linha, index) => ({
    nome: `Trecho ${index + 1}`,
    tipo_rede: "rede",
    fases: Number(linha.fases),
    comprimento_m: Number(linha.comprimento_m),
    corrente_a: Number(linha.corrente_a),
    tensao_nominal_v: Number(linha.fases) === 1 ? 220 : 13800,
    ordem_no_circuito: index + 1,
    consumidores_montante: 20,
    consumidores_jusante: 15,
    fases_montante: Number(linha.fases),
    fases_jusante: Number(linha.fases),
    condutor: obterCondutor(linha.tipo_cabo),
  }));
}

export function montarPayloadCqt(linhasTrecho) {
  return {
    tipo_projeto: "Robustez BT",
    recebeu_leitura_trafo_maxima: true,
    corrente_trafo_a: 110,
    carga_maxima_transformador_kva: 75,
    centro_carga: {
      nome: "CC WEB CQT",
      transformador: {
        descricao: "Trafo 112.5kVA",
        potencia_nominal_kva: 112.5,
        carga_maxima_lida_kva: 75,
        corrente_lida_a: 110,
      },
      trechos: montarTrechosCqt(linhasTrecho),
    },
  };
}
