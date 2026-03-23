import { create } from "zustand";

function obterLinhas(mapa, projetoId, linhaInicialFactory) {
  if (!projetoId) return [linhaInicialFactory(1)];
  const existente = mapa[projetoId];
  if (!existente || existente.length === 0) return [linhaInicialFactory(1)];
  return existente;
}

export const useGridStore = create((set, get) => ({
  linhasCqtPorProjeto: {},
  linhasTracaoPorProjeto: {},

  obterLinhasCqt: (projetoId, linhaInicialFactory) =>
    obterLinhas(get().linhasCqtPorProjeto, projetoId, linhaInicialFactory),

  salvarLinhasCqt: (projetoId, linhas) => {
    if (!projetoId) return;
    set((state) => ({
      linhasCqtPorProjeto: {
        ...state.linhasCqtPorProjeto,
        [projetoId]: linhas,
      },
    }));
  },

  obterLinhasTracao: (projetoId, linhaInicialFactory) =>
    obterLinhas(get().linhasTracaoPorProjeto, projetoId, linhaInicialFactory),

  salvarLinhasTracao: (projetoId, linhas) => {
    if (!projetoId) return;
    set((state) => ({
      linhasTracaoPorProjeto: {
        ...state.linhasTracaoPorProjeto,
        [projetoId]: linhas,
      },
    }));
  },
}));
