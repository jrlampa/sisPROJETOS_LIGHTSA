import { useMemo, useState } from "react";

import { useMutation } from "@tanstack/react-query";

import api from "../lib/api";
import { useProjectStore } from "../store/useProjectStore";

function formatDateTime(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return date.toLocaleString("pt-BR");
}

export function CAD() {
  const { projetoAtivo } = useProjectStore();
  const [file, setFile] = useState(null);
  const [dragOver, setDragOver] = useState(false);

  const projetoId = projetoAtivo?.id || null;

  const mutation = useMutation({
    mutationFn: async () => {
      if (!projetoId) throw new Error("Projeto ativo nao encontrado.");
      if (!file) throw new Error("Selecione um ficheiro .dxf para enviar.");

      const formData = new FormData();
      formData.append("file", file);

      const response = await api.post(`/projetos/${projetoId}/dxf`, formData, {
        headers: {
          "Content-Type": "multipart/form-data",
        },
      });
      return response.data;
    },
  });

  const layersResumo = useMemo(() => mutation.data?.layers || [], [mutation.data]);

  const handleFileSelection = (event) => {
    const selected = event.target.files?.[0] || null;
    if (!selected) return;
    setFile(selected);
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setDragOver(false);
    const dropped = event.dataTransfer.files?.[0] || null;
    if (!dropped) return;
    setFile(dropped);
  };

  if (!projetoId) {
    return (
      <section className="sec-panel" style={{ padding: "16px", color: "#9a3412", fontWeight: 700 }}>
          Nenhum projeto ativo encontrado. Crie ou selecione um projeto no Painel antes de importar DXF.
      </section>
    );
  }

  return (
    <section className="sec-panel">
      <div className="sec-title">Mapeamento CAD / DXF</div>

      <div style={{ padding: 12 }}>
        <label
          htmlFor="dxf-file"
          onDragOver={(event) => {
            event.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={handleDrop}
          style={{
            display: "block",
            border: `2px dashed ${dragOver ? "#3b66ad" : "#8fa1c2"}`,
            borderRadius: 8,
            padding: "22px 14px",
            textAlign: "center",
            background: dragOver ? "#edf3fc" : "#f8fbff",
            cursor: "pointer",
          }}
        >
          <strong style={{ display: "block", marginBottom: 6 }}>Arraste o ficheiro .dxf aqui</strong>
          <span>ou clique para selecionar</span>
          <input id="dxf-file" type="file" accept=".dxf" onChange={handleFileSelection} style={{ display: "none" }} />
        </label>

        <div style={{ marginTop: 10, display: "flex", gap: 8, alignItems: "center", flexWrap: "wrap" }}>
          <div className="result-box" style={{ marginTop: 0, padding: "7px 10px" }}>
            Ficheiro: <strong>{file?.name || "nenhum selecionado"}</strong>
          </div>
          <button type="button" className="btn-primary" onClick={() => mutation.mutate()} disabled={mutation.isPending || !file}>
            Enviar DXF
          </button>
        </div>

        {mutation.isError ? (
          <p className="result-box result-bad" style={{ fontWeight: 700 }}>
            Falha no upload DXF: {mutation.error?.response?.data?.detail || mutation.error?.message || "erro desconhecido"}
          </p>
        ) : null}

        {mutation.isSuccess ? (
          <div className="result-box" style={{ marginTop: 12 }}>
            <p style={{ margin: "4px 0" }}><strong>Total de layers importadas:</strong> {mutation.data.total_layers}</p>
            <p style={{ margin: "4px 0" }}><strong>Segmentos validos:</strong> {mutation.data.total_segmentos}</p>
            <p style={{ margin: "4px 0" }}><strong>Versao DXF:</strong> {mutation.data.versao_dxf}</p>
            <p style={{ margin: "4px 0" }}><strong>Importado em:</strong> {formatDateTime(mutation.data.importado_em)}</p>

            <table className="sec-table" style={{ marginTop: 8 }}>
              <thead>
                <tr>
                  <th>Layer</th>
                  <th>Cor AutoCAD</th>
                  <th>Total Segmentos</th>
                  <th>Comprimento XY</th>
                </tr>
              </thead>
              <tbody>
                {layersResumo.map((layer) => (
                  <tr key={layer.nome}>
                    <td>{layer.nome}</td>
                    <td style={{ textAlign: "center" }}>{layer.cor_autocad}</td>
                    <td style={{ textAlign: "center" }}>{layer.total_segmentos}</td>
                    <td style={{ textAlign: "right" }}>{Number(layer.comprimento_total_xy).toFixed(2)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
      </div>
    </section>
  );
}
