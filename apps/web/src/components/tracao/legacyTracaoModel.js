import {
  mapResultadosPorSecao,
  montarIndexMapTracao,
  montarPostesTracao,
  resumirResultadosTracao,
  toNumberOr,
} from "../../adapters/tracaoAdapter";
import {
  TRAVESSIA_BTZ_VAZIA,
  TRAVESSIA_MT_VAZIA,
  TRAVESSIA_RAL_VAZIA,
  createTravessiasVazias,
  updateTravessia,
} from "./legacyFormConfig";

const STATUS_VAZIO = { mt1: ["-", "-", "-", "-"], mt2: ["-", "-", "-", "-"], bt: ["-", "-", "-", "-"], ral: ["-", "-", "-", "-"] };

const TABELA_CARGAS_POSTE = [
  { alpha: "-", R300: 300, R600: 600 },
  { alpha: 0, R300: 300, R600: 600 },
  { alpha: 5, R300: 299, R600: 598 },
  { alpha: 10, R300: 288, R600: 577 },
  { alpha: 15, R300: 278, R600: 556 },
  { alpha: 20, R300: 268, R600: 536 },
  { alpha: 25, R300: 259, R600: 517 },
  { alpha: 30, R300: 250, R600: 499 },
  { alpha: 40, R300: 232, R600: 464 },
  { alpha: 50, R300: 216, R600: 432 },
  { alpha: 60, R300: 201, R600: 402 },
  { alpha: 70, R300: 187, R600: 374 },
  { alpha: 80, R300: 174, R600: 348 },
  { alpha: 90, R300: 150, R600: 300 },
];

const SECOES_LEGACY = [
  { key: "mt1", titulo: "MT - 1º Nível", tipoPadrao: "Convencional" },
  { key: "mt2", titulo: "MT - 2º Nível", tipoPadrao: "Compacta" },
  { key: "bt", titulo: "BT", tipoPadrao: "Multiplexada" },
  { key: "ral", titulo: "Ramais de Ligação", tipoPadrao: "Ramal" },
];

function criarEstadoInicialTracao() {
  return {
    dadosPoste: {
      orgao: "",
      ns: "",
      projeto: "",
      ponto: "01",
      matricula: "",
      data: "",
      tipoPoste: "Concreto circular",
      modeloPoste: "300",
      coordenadas: "",
    },
    secoes: {
      mt1: createTravessiasVazias(TRAVESSIA_MT_VAZIA),
      mt2: createTravessiasVazias(TRAVESSIA_MT_VAZIA),
      bt: createTravessiasVazias(TRAVESSIA_BTZ_VAZIA),
      ral: createTravessiasVazias(TRAVESSIA_RAL_VAZIA),
    },
  };
}

function normalizarEstadoTracao(estadoBruto) {
  const base = criarEstadoInicialTracao();
  if (!estadoBruto || typeof estadoBruto !== "object") return base;
  return {
    dadosPoste: { ...base.dadosPoste, ...(estadoBruto.dadosPoste || {}) },
    secoes: {
      mt1: Array.isArray(estadoBruto?.secoes?.mt1) ? estadoBruto.secoes.mt1 : base.secoes.mt1,
      mt2: Array.isArray(estadoBruto?.secoes?.mt2) ? estadoBruto.secoes.mt2 : base.secoes.mt2,
      bt: Array.isArray(estadoBruto?.secoes?.bt) ? estadoBruto.secoes.bt : base.secoes.bt,
      ral: Array.isArray(estadoBruto?.secoes?.ral) ? estadoBruto.secoes.ral : base.secoes.ral,
    },
  };
}

function atualizarCampoPoste(prev, campo, valor) {
  return { ...prev, dadosPoste: { ...prev.dadosPoste, [campo]: valor } };
}

function atualizarTravessiaSecao(prev, secao, idx, campo, valor) {
  return {
    ...prev,
    secoes: {
      ...prev.secoes,
      [secao]: updateTravessia(prev.secoes[secao], idx, campo, valor),
    },
  };
}

function montarExecucaoTracao(estadoVisual) {
  const resistenciaNominal = toNumberOr(300, estadoVisual.dadosPoste.modeloPoste);
  const postosEntrada = montarPostesTracao(estadoVisual.secoes, resistenciaNominal);
  return { resistenciaNominal, postosEntrada };
}

function mapearStatusTracao(estadoVisual, postosEntrada, resultados) {
  const indexMap = montarIndexMapTracao(estadoVisual.secoes, postosEntrada);
  return mapResultadosPorSecao(indexMap, resultados || []);
}

function resumoTracao(resultados = []) {
  return resumirResultadosTracao(resultados);
}

function momentoX(travessia) {
  return toNumberOr(0, travessia?.vao) * toNumberOr(0, travessia?.flecha || travessia?.qtdCabos || travessia?.qtdLigacoes);
}

function momentoY(travessia) {
  return toNumberOr(0, travessia?.angulo) * 0.1;
}

export {
  SECOES_LEGACY,
  STATUS_VAZIO,
  TABELA_CARGAS_POSTE,
  atualizarCampoPoste,
  atualizarTravessiaSecao,
  criarEstadoInicialTracao,
  mapearStatusTracao,
  momentoX,
  momentoY,
  montarExecucaoTracao,
  normalizarEstadoTracao,
  resumoTracao,
  toNumberOr,
};
