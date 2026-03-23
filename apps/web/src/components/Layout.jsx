import { Building2, LogOut, UserCircle } from "lucide-react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";

import { useAuthStore } from "../store/useAuthStore";

/* global __APP_VERSION__ */

const linkStyle = ({ isActive }) => ({
  color: isActive ? "#0f172a" : "#1d4ed8",
  textDecoration: "none",
  fontWeight: 700,
  padding: "8px 10px",
  borderRadius: "6px",
  background: isActive ? "#dbeafe" : "transparent",
});

const ROLE_LABEL = {
  ADMIN: "Admin",
  ENGENHEIRO: "Engenheiro",
  CONVIDADO: "Convidado",
};

export function Layout() {
  const navigate = useNavigate();
  const usuario = useAuthStore((s) => s.usuario);
  const logout = useAuthStore((s) => s.logout);
  const appVersion = typeof __APP_VERSION__ !== "undefined" ? __APP_VERSION__ : "0.0.0";

  const handleLogout = () => {
    logout();
    navigate("/login", { replace: true });
  };

  return (
    <div style={{ minHeight: "100vh", background: "#f6f8fc" }}>
      <header
        style={{
          display: "flex",
          alignItems: "center",
          gap: "10px",
          padding: "14px 24px",
          background: "#0f172a",
          color: "#e2e8f0",
          borderBottom: "3px solid #f59e0b",
        }}
      >
        <Building2 size={20} />
        <strong style={{ flex: 1 }}>sisPROJETOS LIGHT S.A.</strong>

        {/* Informação do utilizador logado */}
        {usuario && (
          <div
            style={{
              display: "flex",
              alignItems: "center",
              gap: "10px",
              fontSize: "0.8125rem",
              color: "#94a3b8",
            }}
          >
            <UserCircle size={16} />
            <span>
              <span style={{ color: "#e2e8f0", fontWeight: 600 }}>{usuario.email}</span>
              {" "}·{" "}
              <span
                style={{
                  background: usuario.role === "CONVIDADO" ? "#854d0e" : "#1e3a5f",
                  color: usuario.role === "CONVIDADO" ? "#fef08a" : "#93c5fd",
                  padding: "2px 7px",
                  borderRadius: "999px",
                  fontSize: "0.75rem",
                  fontWeight: 700,
                }}
              >
                {ROLE_LABEL[usuario.role] ?? usuario.role}
              </span>
            </span>
            <button
              type="button"
              onClick={handleLogout}
              title="Sair"
              style={{
                display: "inline-flex",
                alignItems: "center",
                gap: "5px",
                padding: "5px 10px",
                border: "1px solid #334155",
                borderRadius: "6px",
                background: "transparent",
                color: "#cbd5e1",
                fontSize: "0.8125rem",
                fontWeight: 600,
                cursor: "pointer",
              }}
            >
              <LogOut size={14} />
              Sair
            </button>
          </div>
        )}
      </header>

      <main className="page-wrap" style={{ maxWidth: "960px", margin: "14px auto", padding: "24px" }}>
        <nav style={{ marginBottom: "16px", display: "flex", gap: "10px", flexWrap: "wrap" }}>
          <NavLink to="/" style={linkStyle}>
            Painel
          </NavLink>
          <NavLink to="/cqt" style={linkStyle}>
            CQT
          </NavLink>
          <NavLink to="/tracao" style={linkStyle}>
            Tracao
          </NavLink>
          <NavLink to="/cad" style={linkStyle}>
            Mapeamento CAD
          </NavLink>
          <NavLink to="/exportacao" style={linkStyle}>
            Pacote Final
          </NavLink>
        </nav>
        <Outlet />
        <footer
          style={{
            marginTop: "24px",
            color: "#64748b",
            fontSize: "0.75rem",
            textAlign: "right",
          }}
        >
          v{appVersion}
        </footer>
      </main>
    </div>
  );
}
