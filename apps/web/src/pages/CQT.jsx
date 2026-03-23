import { useMemo, useState } from "react";

import { useMutation } from "@tanstack/react-query";
import DataGrid from "react-data-grid";
import "react-data-grid/lib/styles.css";
import { Calculator, PlusCircle } from "lucide-react";

import api from "../lib/api";
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

function obterCondutor(tipoCabo) {
  const nome = (tipoCabo || "").trim();
  if (nome.includes("240")) {
    return { nome, resistencia_ohm_km: 0.15, ampacidade_a: 426 };
  }
  if (nome.includes("70")) {
    return { nome, resistencia_ohm_km: 0.45, ampacidade_a: 140 };
  }
  return { nome: nome || "Condutor Padrao", resistencia_ohm_km: 0.45, ampacidade_a: 140 };
}

export function CQT() {
  const { projetoAtivo } = useProjectStore();
  const [linhasTrecho, setLinhasTrecho] = useState([criarLinhaInicial()]);

  const colunas = useMemo(
    () => [
      { key: "comprimento_m", name: "Comprimento (m)", editable: true },
      { key: "corrente_a", name: "Corrente (A)", editable: true },
      { key: "tipo_cabo", name: "Tipo de Cabo", editable: true },
      { key: "fases", name: "Fases", editable: true },
    ],
    []
  );

  const adicionarLinha = () => {
    setLinhasTrecho((atual) => [...atual, criarLinhaInicial(atual.length + 1)]);
  };

  const mutation = useMutation({
    mutationFn: async () => {
      if (!projetoAtivo?.id) {
        throw new Error("Projeto ativo nao encontrado.");
      }

      const trechos = linhasTrecho.map((linha, index) => ({
        nome: `Trecho ${index + 1}`,
        tipo_rede: "rede",
        fases: Number(linha.fases),
        comprimento_m: Number(linha.comprimento_m),
        corrente_a: Number(linha.corrente_a),
        tensao_nominal_v: Number(linha.fases) === 1 ? 220 : 13800,
        ordem_no_circuito: index + 1,
        consumidores_montante: 20,
        consumidores_jusante: 15,
        fases_montante: Number(linha.fases),
        fases_jusante: Number(linha.fases),
        condutor: obterCondutor(linha.tipo_cabo),
      }));

      const payload = {
        tipo_projeto: "Robustez BT",
        recebeu_leitura_trafo_maxima: true,
        corrente_trafo_a: 110,
        carga_maxima_transformador_kva: 75,
        centro_carga: {
          nome: "CC WEB CQT",
          transformador: {
            descricao: "Trafo 112.5kVA",
            potencia_nominal_kva: 112.5,
            carga_maxima_lida_kva: 75,
            corrente_lida_a: 110,
          },
          trechos,
        },
      };

      const response = await api.post(`/projetos/${projetoAtivo.id}/cqt`, payload);
      return response.data;
    },
  });

  if (!projetoAtivo?.id) {
    return (
      <section
        style={{
          background: "#fff7ed",
          border: "1px solid #fed7aa",
          borderRadius: "12px",
          padding: "18px",
          color: "#9a3412",
          fontWeight: 600,
        }}
      >
        Nenhum projeto ativo encontrado. Crie ou selecione um projeto no Dashboard antes de calcular o CQT.
      </section>
    );
  }

  return (
    <section
      style={{
        background: "white",
        borderRadius: "12px",
        boxShadow: "0 4px 14px rgba(15, 23, 42, 0.08)",
        padding: "20px",
      }}
    >
      <h1 style={{ marginTop: 0, marginBottom: "8px" }}>Etapa 2: CQT</h1>
      <p style={{ marginTop: 0, color: "#475569" }}>
        Preencha os trechos como numa folha de calculo e execute o calculo de queda de tensao.
      </p>

      <div style={{ marginBottom: "10px", display: "flex", gap: "10px", flexWrap: "wrap" }}>
        <button
          type="button"
          onClick={adicionarLinha}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "8px",
            border: "1px solid #cbd5e1",
            borderRadius: "8px",
            padding: "10px 12px",
            background: "#f8fafc",
            cursor: "pointer",
            fontWeight: 600,
          }}
        >
          <PlusCircle size={16} />
          Adicionar Linha
        </button>

        <button
          type="button"
          onClick={() => mutation.mutate()}
          disabled={mutation.isPending}
          style={{
            display: "inline-flex",
            alignItems: "center",
            gap: "8px",
            border: 0,
            borderRadius: "8px",
            padding: "10px 14px",
            background: "#1d4ed8",
            color: "white",
            cursor: "pointer",
            fontWeight: 700,
          }}
        >
          <Calculator size={16} />
          Calcular CQT
        </button>
      </div>

      <DataGrid
        columns={colunas}
        rows={linhasTrecho}
        onRowsChange={setLinhasTrecho}
        rowKeyGetter={(row) => row.id}
        style={{ minHeight: 280, border: "1px solid #e2e8f0" }}
      />

      {mutation.isError ? (
        <p
          style={{
            marginTop: "16px",
            padding: "10px 12px",
            borderRadius: "8px",
            background: "#fee2e2",
            color: "#991b1b",
            fontWeight: 600,
          }}
        >
          Falha no calculo CQT: {mutation.error?.response?.data?.detail || mutation.error?.message || "erro desconhecido"}
        </p>
      ) : null}

      {mutation.isSuccess ? (
        <div
          style={{
            marginTop: "16px",
            padding: "14px",
            borderRadius: "10px",
            background: "#ecfeff",
            border: "1px solid #a5f3fc",
          }}
        >
          <strong style={{ display: "block", marginBottom: "8px" }}>Resultado do CQT</strong>
          <p style={{ margin: "4px 0" }}>
            Queda de Tensão Resultante: {mutation.data?.centro_carga?.queda_total_percent?.toFixed?.(3) ?? mutation.data?.centro_carga?.queda_total_percent ?? "N/A"}%
          </p>
          <p style={{ margin: "4px 0" }}>
            Status do Trafo: {mutation.data?.trafo_dentro_do_limite ? "Dentro do limite" : "Fora do limite"}
          </p>
          <p style={{ margin: "4px 0" }}>
            QDT Total no Limite: {mutation.data?.qdt_total_dentro_do_limite ? "Sim" : "Nao"}
          </p>
        </div>
      ) : null}
    </section>
  );
}
