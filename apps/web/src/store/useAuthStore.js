/**
 * Store de autenticação JWT (Zustand + persist → localStorage).
 *
 * Estado:
 *   token   – JWT raw devolvido pelo backend.
 *   usuario – { email, role } extraído do payload do token.
 *
 * Métodos:
 *   setAuth(token, usuario) – grava token + usuario ao fazer login.
 *   logout()               – limpa o estado e apaga o item do storage.
 */

import { create } from "zustand";
import { persist } from "zustand/middleware";

export const useAuthStore = create(
  persist(
    (set) => ({
      token: null,
      usuario: null,

      setAuth: (token, usuario) => set({ token, usuario }),

      logout: () => set({ token: null, usuario: null }),
    }),
    {
      name: "sisprojetos-auth", // chave no localStorage
    }
  )
);
