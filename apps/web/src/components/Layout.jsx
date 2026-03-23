import { Building2 } from "lucide-react";
import { Link, Outlet } from "react-router-dom";

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

      <main style={{ maxWidth: "960px", margin: "0 auto", padding: "24px" }}>
        <nav style={{ marginBottom: "16px" }}>
          <Link to="/" style={{ color: "#1d4ed8", textDecoration: "none", fontWeight: 600 }}>
            Dashboard
          </Link>
        </nav>
        <Outlet />
      </main>
    </div>
  );
}
