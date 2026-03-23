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

function sanitizeString(str) {
  return String(str ?? "")
    .trim()
    .replace(/<[^>]*>?/gm, "");
}

function toNumberOr(defaultValue, value) {
  const sanitized = sanitizeString(value).replace(/,/g, ".");
  const normalized = sanitized.replace(/[^0-9+\-.]/g, "");
  const number = Number(normalized);
  return Number.isFinite(number) ? number : defaultValue;
}

function sanitizeLinhaTrecho(linha) {
  return {
    ...linha,
    comprimento_m: toNumberOr(LINHA_BASE.comprimento_m, linha.comprimento_m),
    corrente_a: toNumberOr(LINHA_BASE.corrente_a, linha.corrente_a),
    fases: toNumberOr(LINHA_BASE.fases, linha.fases),
    tipo_cabo: sanitizeString(linha.tipo_cabo) || LINHA_BASE.tipo_cabo,
  };
}

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
  const [fatorPotencia, setFatorPotencia] = useState("0.92");

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

      const payload = montarPayloadCqt(linhasTrecho.map(sanitizeLinhaTrecho));

      const response = await api.post(`/projetos/${projetoId}/cqt`, payload);
      return response.data;
    },
  });

  const totalQueda = useMemo(() => mutation.data?.centro_carga?.queda_total_percent, [mutation.data]);
  const totalEsforcos = useMemo(
    () => linhasTrecho.reduce((acc, linha) => acc + toNumberOr(0, linha.corrente_a), 0),
    [linhasTrecho]
  );

  if (!projetoId) {
    return (
      <section className="sec-panel" style={{ padding: "16px", color: "#9a3412", fontWeight: 700 }}>
          Nenhum projeto ativo encontrado. Crie ou selecione um projeto no Painel antes de calcular o CQT.
      </section>
    );
  }

  return (
    <section className="excel-container">
      <table className="excel-table">
        <tbody>
          <tr>
            <td className="excel-td" style={{ fontWeight: 700, textAlign: "center" }}>
              PLANILHA DE CÁLCULO DA QUEDA DE TENSÃO E ESFORÇOS MECÂNICOS DA REDE DE DISTRIBUIÇÃO AÉREA
            </td>
          </tr>
        </tbody>
      </table>

      <table className="excel-table">
        <thead>
          <tr>
            <th className="excel-th-dark" colSpan={4}>
              DADOS DO PROJETO
            </th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <th className="excel-th-light">Nome do Projeto</th>
            <td className="excel-td">
              <input className="excel-input" value={projetoAtivo?.nome || ""} readOnly />
            </td>
            <th className="excel-th-light">Localidade</th>
            <td className="excel-td">
              <input className="excel-input" value={projetoAtivo?.localidade || ""} readOnly />
            </td>
          </tr>
          <tr>
            <th className="excel-th-light">Condutores</th>
            <td className="excel-td">
              <input
                className="excel-input"
                value={linhasTrecho[0]?.tipo_cabo ?? ""}
                onChange={(e) => atualizarLinha(linhasTrecho[0]?.id, "tipo_cabo", e.target.value)}
              />
            </td>
            <th className="excel-th-light">Demanda</th>
            <td className="excel-td">
              <input
                className="excel-input"
                value={linhasTrecho[0]?.corrente_a ?? ""}
                onChange={(e) => atualizarLinha(linhasTrecho[0]?.id, "corrente_a", e.target.value)}
              />
            </td>
          </tr>
          <tr>
            <th className="excel-th-light">Fases</th>
            <td className="excel-td">
              <input
                className="excel-input"
                value={linhasTrecho[0]?.fases ?? ""}
                onChange={(e) => atualizarLinha(linhasTrecho[0]?.id, "fases", e.target.value)}
              />
            </td>
            <th className="excel-th-light">Trechos</th>
            <td className="excel-td">
              <input className="excel-input" value={linhasTrecho.length} readOnly />
            </td>
          </tr>
        </tbody>
      </table>

      <div className="excel-actions">
        <button type="button" className="btn-secondary" onClick={adicionarLinha}>
          <PlusCircle size={14} style={{ marginRight: 6 }} />
          Adicionar Linha
        </button>
        <button type="button" className="btn-primary" onClick={() => mutation.mutate()} disabled={mutation.isPending}>
          <Calculator size={14} style={{ marginRight: 6 }} />
          Calcular Tração
        </button>
      </div>

      <table className="excel-table">
        <thead>
          <tr>
            <th className="excel-th-dark" colSpan={6}>
              Ponto a Ponto - Esforço e Queda de Tensão
            </th>
          </tr>
          <tr>
            <th className="excel-th-light">Trecho</th>
            <th className="excel-th-light">Comp. (m)</th>
            <th className="excel-th-light">Esforços Tração (daN)</th>
            <th className="excel-th-light">Queda Tensão Trecho (%)</th>
            <th className="excel-th-light">Queda Tensão Acum. (%)</th>
            <th className="excel-th-light">Fim de Linha</th>
          </tr>
        </thead>
        <tbody>
          {linhasTrecho.map((linha, idx) => (
            <tr key={linha.id}>
              <td className="excel-td" style={{ textAlign: "center", fontWeight: 700 }}>{`T${idx + 1}`}</td>
              <td className="excel-td">
                <input
                  className="excel-input"
                  value={linha.comprimento_m}
                  onChange={(e) => atualizarLinha(linha.id, "comprimento_m", e.target.value)}
                />
              </td>
              <td className="excel-td">
                <input
                  className="excel-input"
                  value={linha.corrente_a}
                  onChange={(e) => atualizarLinha(linha.id, "corrente_a", e.target.value)}
                />
              </td>
              <td className="excel-td">
                <input
                  className="excel-input"
                  value={linha.queda_tensao_trecho ?? ""}
                  onChange={(e) => atualizarLinha(linha.id, "queda_tensao_trecho", e.target.value)}
                />
              </td>
              <td className="excel-td">
                <input
                  className="excel-input"
                  value={linha.queda_tensao_acumulada ?? ""}
                  onChange={(e) => atualizarLinha(linha.id, "queda_tensao_acumulada", e.target.value)}
                />
              </td>
              <td className="excel-td">
                <select
                  value={linha.fim_linha ?? "Nao"}
                  onChange={(e) => atualizarLinha(linha.id, "fim_linha", e.target.value)}
                >
                  <option value="Nao">Nao</option>
                  <option value="Sim">Sim</option>
                </select>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <table className="excel-table" style={{ maxWidth: "560px" }}>
        <thead>
          <tr>
            <th className="excel-th-dark" colSpan={2}>
              RESUMO DOS ESFORÇOS MECÂNICOS
            </th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <th className="excel-th-light">Esforços Totais (daN)</th>
            <td className="excel-td">
              <input className="excel-input" value={totalEsforcos.toFixed(2)} readOnly />
            </td>
          </tr>
          <tr>
            <th className="excel-th-light">Queda Tensão Acumulada (%)</th>
            <td className="excel-td">
              <input className="excel-input" value={typeof totalQueda === "number" ? totalQueda.toFixed(3) : "N/A"} readOnly />
            </td>
          </tr>
          <tr>
            <th className="excel-th-light">Fator de Potência</th>
            <td className="excel-td">
              <input className="excel-input" value={fatorPotencia} onChange={(e) => setFatorPotencia(e.target.value)} />
            </td>
          </tr>
        </tbody>
      </table>

      {mutation.isError ? (
        <p className="result-box result-bad" style={{ marginBottom: 16 }}>
          Falha no calculo CQT: {mutation.error?.response?.data?.detail || mutation.error?.message || "erro desconhecido"}
        </p>
      ) : null}

      {mutation.isSuccess ? (
        <div className="result-box" style={{ marginBottom: 16 }}>
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
    </section>
  );
}
