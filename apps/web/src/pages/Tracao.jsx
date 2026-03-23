import { useEffect, useMemo, useState } from "react";

import { useMutation } from "@tanstack/react-query";
import { Calculator, PlusCircle } from "lucide-react";

import api from "../lib/api";
import { useGridStore } from "../store/useGridStore";
import { useProjectStore } from "../store/useProjectStore";

const LINHA_BASE = {
  codigo: "PE-001",
  resistencia_nominal_daN: 300,
  comprimento_m: 80,
  tracao_daN: 200,
  tipo_cabo: "CAA 70mm2",
  azimute_graus: 0,
};

function criarLinhaInicial(id = 1) {
  return { id, ...LINHA_BASE };
}

function classeStatusExcel(status) {
  if (status === "APROVADO") return "result-ok";
  if (status === "ALERTA") return "result-warn";
  return "result-bad";
}

export function Tracao() {
  const { projetoAtivo } = useProjectStore();
  const { obterLinhasTracao, salvarLinhasTracao } = useGridStore();

  const [linhas, setLinhas] = useState([criarLinhaInicial()]);

  const projetoId = projetoAtivo?.id || null;

  useEffect(() => {
    if (!projetoId) return;
    const linhasSalvas = obterLinhasTracao(projetoId, criarLinhaInicial);
    setLinhas(linhasSalvas);
  }, [obterLinhasTracao, projetoId]);

  useEffect(() => {
    if (!projetoId) return;
    salvarLinhasTracao(projetoId, linhas);
  }, [linhas, projetoId, salvarLinhasTracao]);

  const adicionarLinha = () => {
    setLinhas((atual) => [...atual, criarLinhaInicial(atual.length + 1)]);
  };

  const atualizarLinha = (id, campo, valor) => {
    setLinhas((atual) =>
      atual.map((linha) => (linha.id === id ? { ...linha, [campo]: valor } : linha))
    );
  };

  const mutation = useMutation({
    mutationFn: async () => {
      if (!projetoId) throw new Error("Projeto ativo nao encontrado.");

      const postes = linhas.map((linha) => ({
        codigo: linha.codigo,
        resistencia_nominal_daN: Number(linha.resistencia_nominal_daN),
        vaos: [
          {
            comprimento_m: Number(linha.comprimento_m),
            tipo_cabo: linha.tipo_cabo,
            tracao_daN: Number(linha.tracao_daN),
            azimute_graus: Number(linha.azimute_graus),
          },
        ],
      }));

      const response = await api.post(`/projetos/${projetoId}/tracao`, { postes });
      return response.data;
    },
  });

  const resultados = useMemo(() => mutation.data?.resultados || [], [mutation.data]);

  if (!projetoId) {
    return (
      <section className="sec-panel" style={{ padding: "16px", color: "#9a3412", fontWeight: 700 }}>
        Nenhum projeto ativo encontrado. Crie ou selecione um projeto no Dashboard antes de calcular a Tracao.
      </section>
    );
  }

  return (
    <section className="sec-panel">
      <div className="sec-title">Etapa 3: Tracao - Planilha</div>

      <div style={{ padding: "10px" }}>
        <div style={{ display: "flex", gap: "8px", marginBottom: "10px", flexWrap: "wrap" }}>
          <button type="button" className="btn-secondary" onClick={adicionarLinha}>
            <PlusCircle size={14} style={{ marginRight: 6 }} />
            Adicionar Linha
          </button>
          <button type="button" className="btn-primary" onClick={() => mutation.mutate()} disabled={mutation.isPending}>
            <Calculator size={14} style={{ marginRight: 6 }} />
            Calcular Tracao
          </button>
        </div>

        <table className="sec-table">
          <thead>
            <tr>
              <th>Poste</th>
              <th>Resistencia (daN)</th>
              <th>Comprimento (m)</th>
              <th>Tracao (daN)</th>
              <th>Tipo de Cabo</th>
              <th>Azimute (graus)</th>
            </tr>
          </thead>
          <tbody>
            {linhas.map((linha) => (
              <tr key={linha.id}>
                <td><input className="xcell" value={linha.codigo} onChange={(e) => atualizarLinha(linha.id, "codigo", e.target.value)} /></td>
                <td><input className="xcell" value={linha.resistencia_nominal_daN} onChange={(e) => atualizarLinha(linha.id, "resistencia_nominal_daN", e.target.value)} /></td>
                <td><input className="xcell" value={linha.comprimento_m} onChange={(e) => atualizarLinha(linha.id, "comprimento_m", e.target.value)} /></td>
                <td><input className="xcell" value={linha.tracao_daN} onChange={(e) => atualizarLinha(linha.id, "tracao_daN", e.target.value)} /></td>
                <td><input className="xcell" value={linha.tipo_cabo} onChange={(e) => atualizarLinha(linha.id, "tipo_cabo", e.target.value)} /></td>
                <td><input className="xcell" value={linha.azimute_graus} onChange={(e) => atualizarLinha(linha.id, "azimute_graus", e.target.value)} /></td>
              </tr>
            ))}
          </tbody>
        </table>

        {mutation.isError ? (
          <p className="result-box result-bad">
            Falha no calculo de Tracao: {mutation.error?.response?.data?.detail || mutation.error?.message || "erro desconhecido"}
          </p>
        ) : null}

        {resultados.length > 0 ? (
          <div style={{ marginTop: "14px" }}>
            <table className="sec-table">
              <thead>
                <tr>
                  <th>Poste</th>
                  <th>Esforco Resultante (daN)</th>
                  <th>Percentual</th>
                  <th>Status Mecanico</th>
                </tr>
              </thead>
              <tbody>
                {resultados.map((resultado, idx) => (
                  <tr key={`resultado-${idx}`}>
                    <td className="xlbl">{linhas[idx]?.codigo || `P${idx + 1}`}</td>
                    <td>{Number(resultado.esforco_resultante_daN || 0).toFixed(2)}</td>
                    <td>{Number(resultado.percentual_carregamento || 0).toFixed(2)}%</td>
                    <td className={classeStatusExcel(resultado.estado_mecanico)} style={{ fontWeight: 700, textAlign: "center" }}>
                      {resultado.estado_mecanico}
                    </td>
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
