/**
 * Página de Login provisório.
 *
 * Pede email + role (dropdown), faz POST /auth/token (mock),
 * armazena o JWT no useAuthStore e redireciona para o Dashboard.
 */

import { useMutation } from "@tanstack/react-query";
import { LogIn } from "lucide-react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";

import api from "../lib/api";
import { useAuthStore } from "../store/useAuthStore";

/** Decodifica o payload de um JWT sem verificar a assinatura. */
function decodeJwtPayload(token) {
  const base64Url = token.split(".")[1];
  const base64 = base64Url.replace(/-/g, "+").replace(/_/g, "/");
  const padding = "==".slice(0, (4 - (base64.length % 4)) % 4);
  return JSON.parse(atob(base64 + padding));
}

export function Login() {
  const navigate = useNavigate();
  const setAuth = useAuthStore((s) => s.setAuth);

  const {
    register,
    handleSubmit,
    formState: { isSubmitting },
  } = useForm({
    defaultValues: { email: "engenheiro@light.com", role: "ENGENHEIRO" },
  });

  const mutation = useMutation({
    mutationFn: async ({ email, role }) => {
      const response = await api.post("/auth/token", { email, role });
      return response.data;
    },
    onSuccess: ({ access_token }) => {
      const payload = decodeJwtPayload(access_token);
      setAuth(access_token, { email: payload.sub, role: payload.role });
      navigate("/", { replace: true });
    },
  });

  const onSubmit = (values) => mutation.mutate(values);

  return (
    <div
      style={{
        minHeight: "100vh",
        background: "#f6f8fc",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
      }}
    >
      <div
        style={{
          background: "white",
          borderRadius: "12px",
          boxShadow: "0 4px 20px rgba(15,23,42,0.12)",
          padding: "36px 32px",
          width: "100%",
          maxWidth: "380px",
        }}
      >
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: "28px" }}>
          <div
            style={{
              display: "inline-flex",
              alignItems: "center",
              justifyContent: "center",
              width: 48,
              height: 48,
              borderRadius: "12px",
              background: "#0f172a",
              marginBottom: "12px",
            }}
          >
            <LogIn size={24} color="#f59e0b" />
          </div>
          <h1 style={{ margin: 0, fontSize: "1.25rem", fontWeight: 700, color: "#0f172a" }}>
            sisPROJETOS LIGHT S.A.
          </h1>
          <p style={{ margin: "4px 0 0", color: "#64748b", fontSize: "0.875rem" }}>
            Acesso ao sistema operacional
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} style={{ display: "grid", gap: "14px" }}>
          <label style={{ display: "grid", gap: "5px", fontSize: "0.875rem", fontWeight: 600, color: "#374151" }}>
            Email
            <input
              {...register("email", { required: true })}
              type="email"
              style={{
                padding: "10px 12px",
                border: "1px solid #cbd5e1",
                borderRadius: "8px",
                fontSize: "0.9375rem",
                outline: "none",
              }}
              placeholder="usuario@light.com"
            />
          </label>

          <label style={{ display: "grid", gap: "5px", fontSize: "0.875rem", fontWeight: 600, color: "#374151" }}>
            Perfil de Acesso
            <select
              {...register("role", { required: true })}
              style={{
                padding: "10px 12px",
                border: "1px solid #cbd5e1",
                borderRadius: "8px",
                fontSize: "0.9375rem",
                background: "white",
                outline: "none",
              }}
            >
              <option value="ADMIN">ADMIN</option>
              <option value="ENGENHEIRO">ENGENHEIRO</option>
              <option value="CONVIDADO">CONVIDADO (leitura)</option>
            </select>
          </label>

          {mutation.isError && (
            <p
              style={{
                margin: 0,
                padding: "10px 12px",
                borderRadius: "8px",
                background: "#fee2e2",
                color: "#991b1b",
                fontSize: "0.875rem",
                fontWeight: 600,
              }}
            >
              {mutation.error?.response?.data?.detail ||
                mutation.error?.message ||
                "Falha ao autenticar. Tente novamente."}
            </p>
          )}

          <button
            type="submit"
            disabled={isSubmitting || mutation.isPending}
            style={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: "8px",
              padding: "11px 14px",
              border: 0,
              borderRadius: "8px",
              background: mutation.isPending ? "#93c5fd" : "#1d4ed8",
              color: "white",
              fontWeight: 700,
              fontSize: "0.9375rem",
              cursor: mutation.isPending ? "not-allowed" : "pointer",
              transition: "background 0.15s",
            }}
          >
            <LogIn size={16} />
            {mutation.isPending ? "Autenticando…" : "Entrar"}
          </button>
        </form>

        <p
          style={{
            marginTop: "20px",
            textAlign: "center",
            fontSize: "0.75rem",
            color: "#94a3b8",
          }}
        >
          Acesso provisório — integração SSO em breve.
        </p>
      </div>
    </div>
  );
}
