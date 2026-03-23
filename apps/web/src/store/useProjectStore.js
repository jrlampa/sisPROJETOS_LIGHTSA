import { create } from "zustand";
import { persist } from "zustand/middleware";

export const useProjectStore = create(
  persist(
    (set) => ({
      projetoAtivo: null,
      setProjetoAtivo: (projeto) => set({ projetoAtivo: projeto }),
      limparProjetoAtivo: () => set({ projetoAtivo: null }),
    }),
    {
      name: "sisprojetos-project",
    }
  )
);
