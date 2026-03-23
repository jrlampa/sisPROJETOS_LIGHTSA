import { Component } from "react";

export class ErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error) {
    // Mantem rastreabilidade local sem expor detalhes tecnicos ao utilizador.
    console.error("Erro de interface capturado pelo ErrorBoundary:", error);
  }

  handleReload = () => {
    window.location.reload();
  };

  render() {
    if (this.state.hasError) {
      return (
        <div
          style={{
            minHeight: "100vh",
            display: "grid",
            placeItems: "center",
            background: "#f8fafc",
            padding: "24px",
          }}
        >
          <div
            style={{
              width: "100%",
              maxWidth: "520px",
              background: "#ffffff",
              border: "1px solid #e2e8f0",
              borderRadius: "14px",
              padding: "24px",
              boxShadow: "0 12px 30px rgba(15, 23, 42, 0.08)",
              textAlign: "center",
            }}
          >
            <h1 style={{ margin: 0, fontSize: "1.35rem", color: "#0f172a" }}>
              Ups! Algo correu mal na interface
            </h1>
            <p style={{ margin: "12px 0 20px", color: "#475569", lineHeight: 1.5 }}>
              Ocorreu uma falha inesperada de renderizacao. Recarregue a pagina para tentar
              novamente.
            </p>
            <button
              type="button"
              onClick={this.handleReload}
              style={{
                border: 0,
                borderRadius: "10px",
                background: "#1d4ed8",
                color: "#ffffff",
                fontWeight: 700,
                padding: "10px 16px",
                cursor: "pointer",
              }}
            >
              Recarregar pagina
            </button>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}
