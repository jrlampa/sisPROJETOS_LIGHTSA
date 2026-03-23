const LINHA_BASE = {
  poste: "",
  vao_m: 30,
  corrente_a: 35,
  esforco_dan: 35,
  tipo_cabo: "240 Al - Arm",
  fases: 3,
  queda_tensao_trecho: "",
  queda_tensao_acumulada: "",
  fim_linha: "Nao",
};

function sanitizeString(str) {
  return String(str ?? "")
    .trim()
    .replace(/<[^>]*>?/gm, "");
}

function toNumberOr(defaultValue, value) {
  const sanitized = sanitizeString(value).replace(/,/g, ".");
  const normalized = sanitized.replace(/[^0-9+\-.]/g, "");
  const number = Number(normalized);
  return Number.isFinite(number) ? number : defaultValue;
}

function criarLinhaInicial(id = 1) {
  return {
    id,
    ...LINHA_BASE,
  };
}

function criarCabecalhoInicial(projetoAtivo) {
  const hoje = new Date();
  const data = `${String(hoje.getDate()).padStart(2, "0")}/${String(hoje.getMonth() + 1).padStart(2, "0")}/${hoje.getFullYear()}`;

  return {
    nomeProjeto: projetoAtivo?.nome || "",
    projetista: "",
    data,
    localidade: projetoAtivo?.localidade || "",
    condutores: LINHA_BASE.tipo_cabo,
    demanda: String(LINHA_BASE.corrente_a),
    trafoKva: "112.5",
    tensao: "220",
    fatorPotencia: "0.92",
    observacoes: "",
  };
}

function criarEstadoLadoInicial(projetoAtivo) {
  return {
    cabecalho: criarCabecalhoInicial(projetoAtivo),
    trechos: [criarLinhaInicial(1)],
  };
}

function normalizarEstadoLado(estadoBruto, projetoAtivo) {
  const inicial = criarEstadoLadoInicial(projetoAtivo);

  if (!estadoBruto || typeof estadoBruto !== "object") {
    return inicial;
  }

  const trechosBrutos = Array.isArray(estadoBruto?.trechos)
    ? estadoBruto.trechos
    : Array.isArray(estadoBruto)
      ? estadoBruto
      : inicial.trechos;

  const trechos = (trechosBrutos.length ? trechosBrutos : [criarLinhaInicial(1)]).map((linha, idx) => ({
    ...LINHA_BASE,
    ...linha,
    id: Number.isFinite(Number(linha?.id)) ? Number(linha.id) : idx + 1,
  }));

  return {
    cabecalho: { ...inicial.cabecalho, ...(estadoBruto?.cabecalho || {}) },
    trechos,
  };
}

function sanitizeLinhaTrecho(linha) {
  return {
    comprimento_m: toNumberOr(LINHA_BASE.vao_m, linha.vao_m),
    corrente_a: toNumberOr(LINHA_BASE.corrente_a, linha.corrente_a),
    fases: toNumberOr(LINHA_BASE.fases, linha.fases),
    tipo_cabo: sanitizeString(linha.tipo_cabo) || LINHA_BASE.tipo_cabo,
    queda_tensao_trecho: linha.queda_tensao_trecho,
    queda_tensao_acumulada: linha.queda_tensao_acumulada,
    fim_linha: linha.fim_linha,
  };
}

export {
  LINHA_BASE,
  criarEstadoLadoInicial,
  criarLinhaInicial,
  normalizarEstadoLado,
  sanitizeLinhaTrecho,
  toNumberOr,
};
