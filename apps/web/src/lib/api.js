/**
 * Cliente HTTP Axios centralizado.
 *
 * Request interceptor  — injeta `Authorization: Bearer <token>` em todos
 *                         os pedidos quando o utilizador está autenticado.
 * Response interceptor — intercepta erros 401 (token expirado / inválido),
 *                         chama logout() e redireciona para /login.
 */

import axios from "axios";

// Import circular-safe: useAuthStore expõe getState() fora do React
import { useAuthStore } from "../store/useAuthStore";

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || "http://localhost:8000",
  timeout: 15000,
  headers: {
    "Content-Type": "application/json",
  },
});

// ---------------------------------------------------------------------------
// Request interceptor — injeta o Bearer token se disponível
// ---------------------------------------------------------------------------
api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().token;
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// ---------------------------------------------------------------------------
// Response interceptor — trata 401 (sessão expirada)
// ---------------------------------------------------------------------------
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === "ERR_NETWORK") {
      window.alert("Servidor inacessivel. Verifique a sua ligacao.");
      return Promise.reject(error);
    }

    if (error.response?.status === 401) {
      useAuthStore.getState().logout();
      // Redireciona para login — window.location porque o interceptor está
      // fora do contexto React e não pode usar useNavigate.
      window.location.href = "/login";
    }
    return Promise.reject(error);
  }
);

export default api;
