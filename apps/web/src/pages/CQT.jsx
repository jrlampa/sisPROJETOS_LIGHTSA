import { useEffect, useMemo, useState } from "react";

import { useMutation } from "@tanstack/react-query";
import { Calculator, PlusCircle } from "lucide-react";

import { montarPayloadCqt } from "../adapters/cqtAdapter";
import { LegacyExcelHeader } from "../components/cqt/LegacyExcelHeader";
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
    queda_tensao_trecho: "",
    queda_tensao_acumulada: "",
    fim_linha: "Nao",
    resistencia_equivalente: "",
    reatancia_equivalente: "",
    produto_ir: "",
    produto_ix: "",
    ...LINHA_BASE,
  };
}

function criarCabecalhoInicial(projetoAtivo) {
  const hoje = new Date();
  const data = `${String(hoje.getDate()).padStart(2, "0")}/${String(hoje.getMonth() + 1).padStart(2, "0")}/${hoje.getFullYear()}`;
  return {
    nomeProjeto: projetoAtivo?.nome || "",
    projetista: "",
    data,
    localidade: projetoAtivo?.localidade || "",
    condutores: LINHA_BASE.tipo_cabo,
    demanda: String(LINHA_BASE.corrente_a),
    trafoKva: "112.5",
    tensao: "13800",
    fatorPotencia: "0.92",
    observacoes: "",
  };
}

function criarEstadoVisualInicial(projetoAtivo) {
  const cabecalho = criarCabecalhoInicial(projetoAtivo);
  return {
    esquerdo: {
      cabecalho: { ...cabecalho },
      trechos: [criarLinhaInicial(1)],
    },
    direito: {
      cabecalho: { ...cabecalho },
      trechos: [criarLinhaInicial(1)],
    },
  };
}

function normalizarEstadoVisual(estadoBruto, projetoAtivo) {
  if (!estadoBruto || typeof estadoBruto !== "object") {
    return criarEstadoVisualInicial(projetoAtivo);
  }

  if (Array.isArray(estadoBruto)) {
    const inicial = criarEstadoVisualInicial(projetoAtivo);
    return {
      esquerdo: { ...inicial.esquerdo, trechos: estadoBruto.length ? estadoBruto : [criarLinhaInicial(1)] },
      direito: { ...inicial.direito, trechos: [criarLinhaInicial(1)] },
    };
  }

  const inicial = criarEstadoVisualInicial(projetoAtivo);
  const esquerdoTrechos = Array.isArray(estadoBruto?.esquerdo?.trechos) ? estadoBruto.esquerdo.trechos : inicial.esquerdo.trechos;
  const direitoTrechos = Array.isArray(estadoBruto?.direito?.trechos) ? estadoBruto.direito.trechos : inicial.direito.trechos;

  return {
    esquerdo: {
      cabecalho: { ...inicial.esquerdo.cabecalho, ...(estadoBruto?.esquerdo?.cabecalho || {}) },
      trechos: esquerdoTrechos.length ? esquerdoTrechos : [criarLinhaInicial(1)],
    },
    direito: {
      cabecalho: { ...inicial.direito.cabecalho, ...(estadoBruto?.direito?.cabecalho || {}) },
      trechos: direitoTrechos.length ? direitoTrechos : [criarLinhaInicial(1)],
    },
  };
}

export function CQT() {
  const { projetoAtivo } = useProjectStore();
  const { obterLinhasCqt, salvarLinhasCqt } = useGridStore();
  const [abaAtiva, setAbaAtiva] = useState("esquerdo");
  const [estadoVisual, setEstadoVisual] = useState(() => criarEstadoVisualInicial(projetoAtivo));

  const projetoId = projetoAtivo?.id || null;

  useEffect(() => {
    if (!projetoId) return;
    const estadoSalvo = obterLinhasCqt(projetoId, () => criarEstadoVisualInicial(projetoAtivo));
    setEstadoVisual(normalizarEstadoVisual(estadoSalvo, projetoAtivo));
  }, [obterLinhasCqt, projetoAtivo, projetoId]);

  useEffect(() => {
    if (!projetoId) return;
    salvarLinhasCqt(projetoId, estadoVisual);
  }, [estadoVisual, projetoId, salvarLinhasCqt]);

  const ladoAtivo = estadoVisual[abaAtiva];
  const trechosAtivos = ladoAtivo.trechos;

  const adicionarLinha = () => {
    setEstadoVisual((atual) => {
      const atuais = atual[abaAtiva].trechos;
      return {
        ...atual,
        [abaAtiva]: {
          ...atual[abaAtiva],
          trechos: [...atuais, criarLinhaInicial(atuais.length + 1)],
        },
      };
    });
  };

  const atualizarLinha = (id, campo, valor) => {
    setEstadoVisual((atual) => ({
      ...atual,
      [abaAtiva]: {
        ...atual[abaAtiva],
        trechos: atual[abaAtiva].trechos.map((linha) => (linha.id === id ? { ...linha, [campo]: valor } : linha)),
      },
    }));
  };

  const atualizarCabecalho = (campo, valor) => {
    setEstadoVisual((atual) => ({
      ...atual,
      [abaAtiva]: {
        ...atual[abaAtiva],
        cabecalho: {
          ...atual[abaAtiva].cabecalho,
          [campo]: valor,
        },
      },
    }));
  };

  const mutation = useMutation({
    mutationFn: async () => {
      if (!projetoId) {
        throw new Error("Projeto ativo nao encontrado.");
      }

      const payload = montarPayloadCqt(trechosAtivos.map(sanitizeLinhaTrecho));

      const response = await api.post(`/projetos/${projetoId}/cqt`, payload);
      return response.data;
    },
  });

  const totalQueda = useMemo(() => mutation.data?.centro_carga?.queda_total_percent, [mutation.data]);
  const totalEsforcos = useMemo(
    () => trechosAtivos.reduce((acc, linha) => acc + toNumberOr(0, linha.corrente_a), 0),
    [trechosAtivos]
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
      <div className="excel-tabs">
        <button
          type="button"
          className={`excel-tab ${abaAtiva === "esquerdo" ? "excel-tab-active" : ""}`}
          onClick={() => setAbaAtiva("esquerdo")}
        >
          CÁLCULO - LADO ESQUERDO
        </button>
        <button
          type="button"
          className={`excel-tab ${abaAtiva === "direito" ? "excel-tab-active" : ""}`}
          onClick={() => setAbaAtiva("direito")}
        >
          CÁLCULO - LADO DIREITO
        </button>
      </div>

      <table className="excel-table">
        <tbody>
          <tr>
            <td className="excel-td" style={{ fontWeight: 700, textAlign: "center" }}>
              PLANILHA DE CÁLCULO DA QUEDA DE TENSÃO E ESFORÇOS MECÂNICOS DA REDE DE DISTRIBUIÇÃO AÉREA
            </td>
          </tr>
        </tbody>
      </table>

      <LegacyExcelHeader
        dadosCabecalho={ladoAtivo.cabecalho}
        onChangeCampo={atualizarCabecalho}
        tituloAba={abaAtiva === "esquerdo" ? "CÁLCULO - LADO ESQUERDO" : "CÁLCULO - LADO DIREITO"}
      />

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
            <th className="excel-th-dark" colSpan={13}>
              Ponto a Ponto - Esforço e Queda de Tensão
            </th>
          </tr>
          <tr>
            <th className="excel-th-light">Trecho</th>
            <th className="excel-th-light">Comp. (m)</th>
            <th className="excel-th-light">Corrente (A)</th>
            <th className="excel-th-light">Tipo Cabo</th>
            <th className="excel-th-light">Fases</th>
            <th className="excel-th-light">R eq (Ω)</th>
            <th className="excel-th-light">X eq (Ω)</th>
            <th className="excel-th-light">I x R</th>
            <th className="excel-th-light">I x X</th>
            <th className="excel-th-light">Esforços Tração (daN)</th>
            <th className="excel-th-light">Queda Tensão Trecho (%)</th>
            <th className="excel-th-light">Queda Tensão Acum. (%)</th>
            <th className="excel-th-light">Fim de Linha</th>
          </tr>
        </thead>
        <tbody>
          {trechosAtivos.map((linha, idx) => (
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
                  value={linha.tipo_cabo}
                  onChange={(e) => atualizarLinha(linha.id, "tipo_cabo", e.target.value)}
                />
              </td>
              <td className="excel-td">
                <input className="excel-input" value={linha.fases} onChange={(e) => atualizarLinha(linha.id, "fases", e.target.value)} />
              </td>
              <td className="excel-td">
                <input
                  className="excel-input"
                  value={linha.resistencia_equivalente ?? ""}
                  onChange={(e) => atualizarLinha(linha.id, "resistencia_equivalente", e.target.value)}
                />
              </td>
              <td className="excel-td">
                <input
                  className="excel-input"
                  value={linha.reatancia_equivalente ?? ""}
                  onChange={(e) => atualizarLinha(linha.id, "reatancia_equivalente", e.target.value)}
                />
              </td>
              <td className="excel-td">
                <input className="excel-input" value={linha.produto_ir ?? ""} onChange={(e) => atualizarLinha(linha.id, "produto_ir", e.target.value)} />
              </td>
              <td className="excel-td">
                <input className="excel-input" value={linha.produto_ix ?? ""} onChange={(e) => atualizarLinha(linha.id, "produto_ix", e.target.value)} />
              </td>
              <td className="excel-td">
                <input
                  className="excel-input"
                  value={linha.esforco_tracao ?? linha.corrente_a}
                  onChange={(e) => atualizarLinha(linha.id, "esforco_tracao", e.target.value)}
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
            <th className="excel-th-dark" colSpan={4}>
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
            <th className="excel-th-light">Fator de Potência</th>
            <td className="excel-td">
              <input
                className="excel-input"
                value={ladoAtivo.cabecalho.fatorPotencia}
                onChange={(e) => atualizarCabecalho("fatorPotencia", e.target.value)}
              />
            </td>
          </tr>
          <tr>
            <th className="excel-th-light">Queda Tensão Acumulada (%)</th>
            <td className="excel-td">
              <input className="excel-input" value={typeof totalQueda === "number" ? totalQueda.toFixed(3) : "N/A"} readOnly />
            </td>
            <th className="excel-th-light">Status Trafo</th>
            <td className="excel-td">
              <input
                className="excel-input"
                value={mutation.data?.trafo_dentro_do_limite ? "Dentro do limite" : "Aguardando cálculo"}
                readOnly
              />
            </td>
          </tr>
          <tr>
            <th className="excel-th-light">QDT Total no Limite</th>
            <td className="excel-td">
              <input
                className="excel-input"
                value={mutation.data?.qdt_total_dentro_do_limite ? "Sim" : "Aguardando cálculo"}
                readOnly
              />
            </td>
            <th className="excel-th-light">Observações</th>
            <td className="excel-td">
              <input
                className="excel-input"
                value={ladoAtivo.cabecalho.observacoes}
                onChange={(e) => atualizarCabecalho("observacoes", e.target.value)}
              />
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
