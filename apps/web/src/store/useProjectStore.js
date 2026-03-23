import { create } from "zustand";

export const useProjectStore = create((set) => ({
  projetoAtivo: null,
  setProjetoAtivo: (projeto) => set({ projetoAtivo: projeto }),
  limparProjetoAtivo: () => set({ projetoAtivo: null }),
}));
