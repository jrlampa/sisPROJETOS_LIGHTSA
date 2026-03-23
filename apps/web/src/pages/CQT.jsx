import { useEffect, useMemo, useState } from "react";

import { useMutation } from "@tanstack/react-query";
import { Calculator, PlusCircle } from "lucide-react";

import { montarPayloadCqt } from "../adapters/cqtAdapter";
import api from "../lib/api";
import { useGridStore } from "../store/useGridStore";
import { useProjectStore } from "../store/useProjectStore";

const LINHA_BASE = {
  comprimento_m: 120,
  corrente_a: 35,
  tipo_cabo: "240 Al - Arm",
  fases: 3,
};

function criarLinhaInicial(id = 1) {
  return {
    id,
    ...LINHA_BASE,
  };
}

export function CQT() {
  const { projetoAtivo } = useProjectStore();
  const { obterLinhasCqt, salvarLinhasCqt } = useGridStore();
  const [linhasTrecho, setLinhasTrecho] = useState([criarLinhaInicial()]);

  const projetoId = projetoAtivo?.id || null;

  useEffect(() => {
    if (!projetoId) return;
    const linhasSalvas = obterLinhasCqt(projetoId, criarLinhaInicial);
    setLinhasTrecho(linhasSalvas);
  }, [obterLinhasCqt, projetoId]);

  useEffect(() => {
    if (!projetoId) return;
    salvarLinhasCqt(projetoId, linhasTrecho);
  }, [linhasTrecho, projetoId, salvarLinhasCqt]);

  const adicionarLinha = () => {
    setLinhasTrecho((atual) => [...atual, criarLinhaInicial(atual.length + 1)]);
  };

  const atualizarLinha = (id, campo, valor) => {
    setLinhasTrecho((atual) =>
      atual.map((linha) => (linha.id === id ? { ...linha, [campo]: valor } : linha))
    );
  };

  const mutation = useMutation({
    mutationFn: async () => {
      if (!projetoId) {
        throw new Error("Projeto ativo nao encontrado.");
      }

      const payload = montarPayloadCqt(linhasTrecho);

      const response = await api.post(`/projetos/${projetoId}/cqt`, payload);
      return response.data;
    },
  });

  const totalQueda = useMemo(() => mutation.data?.centro_carga?.queda_total_percent, [mutation.data]);

  if (!projetoId) {
    return (
      <section className="sec-panel" style={{ padding: "16px", color: "#9a3412", fontWeight: 700 }}>
          Nenhum projeto ativo encontrado. Crie ou selecione um projeto no Painel antes de calcular o CQT.
      </section>
    );
  }

  return (
    <section className="sec-panel">
      <div className="sec-title">Etapa 2: CQT - Planilha</div>

      <div style={{ padding: "10px" }}>
        <div style={{ display: "flex", gap: "8px", marginBottom: "10px", flexWrap: "wrap" }}>
          <button type="button" className="btn-secondary" onClick={adicionarLinha}>
            <PlusCircle size={14} style={{ marginRight: 6 }} />
            Adicionar Linha
          </button>
          <button type="button" className="btn-primary" onClick={() => mutation.mutate()} disabled={mutation.isPending}>
            <Calculator size={14} style={{ marginRight: 6 }} />
            Calcular CQT
          </button>
        </div>

        <table className="sec-table">
          <thead>
            <tr>
              <th style={{ width: 80 }}>Trecho</th>
              <th>Comprimento (m)</th>
              <th>Corrente (A)</th>
              <th>Tipo de Cabo</th>
              <th>Fases</th>
            </tr>
          </thead>
          <tbody>
            {linhasTrecho.map((linha, idx) => (
              <tr key={linha.id}>
                <td className="xlbl">T{idx + 1}</td>
                <td>
                  <input
                    className="xcell"
                    value={linha.comprimento_m}
                    onChange={(e) => atualizarLinha(linha.id, "comprimento_m", e.target.value)}
                  />
                </td>
                <td>
                  <input
                    className="xcell"
                    value={linha.corrente_a}
                    onChange={(e) => atualizarLinha(linha.id, "corrente_a", e.target.value)}
                  />
                </td>
                <td>
                  <input
                    className="xcell"
                    value={linha.tipo_cabo}
                    onChange={(e) => atualizarLinha(linha.id, "tipo_cabo", e.target.value)}
                  />
                </td>
                <td>
                  <input
                    className="xcell"
                    value={linha.fases}
                    onChange={(e) => atualizarLinha(linha.id, "fases", e.target.value)}
                  />
                </td>
              </tr>
            ))}
          </tbody>
        </table>

        {mutation.isError ? (
          <p className="result-box result-bad">
            Falha no calculo CQT: {mutation.error?.response?.data?.detail || mutation.error?.message || "erro desconhecido"}
          </p>
        ) : null}

        {mutation.isSuccess ? (
          <div className="result-box">
            <p style={{ margin: "2px 0" }}>
              <strong>Queda de Tensao Resultante:</strong> {typeof totalQueda === "number" ? totalQueda.toFixed(3) : "N/A"}%
            </p>
            <p style={{ margin: "2px 0" }}>
              <strong>Status do Trafo:</strong> {mutation.data?.trafo_dentro_do_limite ? "Dentro do limite" : "Fora do limite"}
            </p>
            <p style={{ margin: "2px 0" }}>
              <strong>QDT Total no Limite:</strong> {mutation.data?.qdt_total_dentro_do_limite ? "Sim" : "Nao"}
            </p>
          </div>
        ) : null}
      </div>
    </section>
  );
}
