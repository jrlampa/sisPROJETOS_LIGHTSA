import { useState } from "react";

import { useMutation } from "@tanstack/react-query";
import { CheckCircle2, Download, FileArchive } from "lucide-react";

import api from "../lib/api";
import { useProjectStore } from "../store/useProjectStore";

function getApiBaseUrl() {
  return import.meta.env.VITE_API_BASE_URL || api.defaults.baseURL || "http://localhost:8000";
}

export function Exportacao() {
  const { projetoAtivo } = useProjectStore();
  const [pacoteGerado, setPacoteGerado] = useState(null);

  const projetoId = projetoAtivo?.id || null;

  const mutation = useMutation({
    mutationFn: async () => {
      if (!projetoId) {
        throw new Error("Projeto ativo nao encontrado.");
      }
      const response = await api.post(`/projetos/${projetoId}/exportacao/gerar`);
      return response.data;
    },
    onSuccess: (data) => {
      setPacoteGerado(data?.pacote || null);
    },
  });

  const handleDownload = () => {
    if (!projetoId) return;
    const baseUrl = getApiBaseUrl().replace(/\/$/, "");
    const downloadUrl = `${baseUrl}/projetos/${projetoId}/exportacao/download`;

    const link = document.createElement("a");
    link.href = downloadUrl;
    link.target = "_blank";
    link.rel = "noopener";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
  };

  if (!projetoId) {
    return (
      <section className="sec-panel" style={{ padding: "16px", color: "#9a3412", fontWeight: 700 }}>
        Nenhum projeto ativo encontrado. Crie ou selecione um projeto no Dashboard antes de gerar o pacote final.
      </section>
    );
  }

  return (
    <section className="sec-panel">
      <div className="sec-title">Onda 5 - Relatorios e Pacote Final</div>

      <div style={{ padding: 14 }}>
        <p style={{ margin: "0 0 10px" }}>
          Pronto para gerar os relatorios do Projeto ID: <strong>{projetoId}</strong>
        </p>

        <button
          type="button"
          className="btn-primary"
          style={{ display: "inline-flex", alignItems: "center", gap: 6 }}
          onClick={() => mutation.mutate()}
          disabled={mutation.isPending}
        >
          <FileArchive size={15} />
          {mutation.isPending ? "Loading..." : "Gerar Pacote Tecnico (ZIP)"}
        </button>

        {mutation.isError ? (
          <p className="result-box result-bad" style={{ fontWeight: 700 }}>
            Falha ao gerar pacote: {mutation.error?.response?.data?.detail || mutation.error?.message || "erro desconhecido"}
          </p>
        ) : null}

        {mutation.isSuccess && pacoteGerado ? (
          <div className="result-box result-ok" style={{ marginTop: 12, borderColor: "#7ca982" }}>
            <p style={{ margin: "0 0 8px", display: "flex", alignItems: "center", gap: 8, fontWeight: 700 }}>
              <CheckCircle2 size={16} />
              Pacote tecnico gerado com sucesso.
            </p>
            <p style={{ margin: "0 0 8px" }}>Status: <strong>{pacoteGerado.status}</strong></p>
            <button
              type="button"
              className="btn-success"
              onClick={handleDownload}
              style={{ display: "inline-flex", alignItems: "center", gap: 6 }}
            >
              <Download size={15} />
              Baixar Arquivo ZIP
            </button>
          </div>
        ) : null}
      </div>
    </section>
  );
}
