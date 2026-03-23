import { Building2 } from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";

const linkStyle = ({ isActive }) => ({
  color: isActive ? "#0f172a" : "#1d4ed8",
  textDecoration: "none",
  fontWeight: 700,
  padding: "8px 10px",
  borderRadius: "6px",
  background: isActive ? "#dbeafe" : "transparent",
});

export function Layout() {
  return (
    <div style={{ minHeight: "100vh", background: "#f6f8fc" }}>
      <header
        style={{
          display: "flex",
          alignItems: "center",
          gap: "10px",
          padding: "16px 24px",
          background: "#0f172a",
          color: "#e2e8f0",
          borderBottom: "3px solid #f59e0b",
        }}
      >
        <Building2 size={20} />
        <strong>sisPROJETOS LIGHT S.A.</strong>
      </header>

      <main className="page-wrap" style={{ maxWidth: "960px", margin: "14px auto", padding: "24px" }}>
        <nav style={{ marginBottom: "16px", display: "flex", gap: "10px", flexWrap: "wrap" }}>
          <NavLink to="/" style={linkStyle}>
            Dashboard
          </NavLink>
          <NavLink to="/cqt" style={linkStyle}>
            CQT
          </NavLink>
          <NavLink to="/tracao" style={linkStyle}>
            Tracao
          </NavLink>
        </nav>
        <Outlet />
      </main>
    </div>
  );
}
