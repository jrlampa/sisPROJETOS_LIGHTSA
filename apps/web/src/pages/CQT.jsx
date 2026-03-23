import { useEffect, useMemo, useState } from "react";

import { useMutation } from "@tanstack/react-query";
import { Calculator, PlusCircle } from "lucide-react";

import { montarPayloadCqt } from "../adapters/cqtAdapter";
import { LegacyExcelHeader } from "../components/cqt/LegacyExcelHeader";
import api from "../lib/api";
import { useGridStore } from "../store/useGridStore";
import { useProjectStore } from "../store/useProjectStore";

const LINHA_BASE = {
  poste: "",
  vao_m: 30,
  corrente_a: 35,
  esforco_dan: 35,
  tipo_cabo: "240 Al - Arm",
  fases: 3,
  queda_tensao_trecho: "",
  queda_tensao_acumulada: "",
  fim_linha: "Nao",
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

function criarLinhaInicial(id = 1) {
  return {
    id,
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
    tensao: "220",
    fatorPotencia: "0.92",
    observacoes: "",
  };
}

function criarEstadoLadoInicial(projetoAtivo) {
  return {
    cabecalho: criarCabecalhoInicial(projetoAtivo),
    trechos: [criarLinhaInicial(1)],
  };
}

function normalizarEstadoLado(estadoBruto, projetoAtivo) {
  const inicial = criarEstadoLadoInicial(projetoAtivo);

  if (!estadoBruto || typeof estadoBruto !== "object") {
    return inicial;
  }

  const trechosBrutos = Array.isArray(estadoBruto?.trechos)
    ? estadoBruto.trechos
    : Array.isArray(estadoBruto)
      ? estadoBruto
      : inicial.trechos;

  const trechos = (trechosBrutos.length ? trechosBrutos : [criarLinhaInicial(1)]).map((linha, idx) => ({
    ...LINHA_BASE,
    ...linha,
    id: Number.isFinite(Number(linha?.id)) ? Number(linha.id) : idx + 1,
  }));

  return {
    cabecalho: { ...inicial.cabecalho, ...(estadoBruto?.cabecalho || {}) },
    trechos,
  };
}

function sanitizeLinhaTrecho(linha) {
  return {
    comprimento_m: toNumberOr(LINHA_BASE.vao_m, linha.vao_m),
    corrente_a: toNumberOr(LINHA_BASE.corrente_a, linha.corrente_a),
    fases: toNumberOr(LINHA_BASE.fases, linha.fases),
    tipo_cabo: sanitizeString(linha.tipo_cabo) || LINHA_BASE.tipo_cabo,
    queda_tensao_trecho: linha.queda_tensao_trecho,
    queda_tensao_acumulada: linha.queda_tensao_acumulada,
    fim_linha: linha.fim_linha,
  };
}

export function CQT() {
  const { projetoAtivo } = useProjectStore();
  const { obterLinhasCqt, salvarLinhasCqt } = useGridStore();

  const [abaAtiva, setAbaAtiva] = useState("esquerdo");
  const [estadoEsquerdo, setEstadoEsquerdo] = useState(() => criarEstadoLadoInicial(projetoAtivo));
  const [estadoDireito, setEstadoDireito] = useState(() => criarEstadoLadoInicial(projetoAtivo));

  const projetoId = projetoAtivo?.id || null;

  useEffect(() => {
    if (!projetoId) return;

    const estadoSalvo = obterLinhasCqt(projetoId, () => ({
      esquerdo: criarEstadoLadoInicial(projetoAtivo),
      direito: criarEstadoLadoInicial(projetoAtivo),
    }));

    if (Array.isArray(estadoSalvo)) {
      setEstadoEsquerdo(normalizarEstadoLado(estadoSalvo, projetoAtivo));
      setEstadoDireito(criarEstadoLadoInicial(projetoAtivo));
      return;
    }

    setEstadoEsquerdo(normalizarEstadoLado(estadoSalvo?.esquerdo, projetoAtivo));
    setEstadoDireito(normalizarEstadoLado(estadoSalvo?.direito, projetoAtivo));
  }, [obterLinhasCqt, projetoAtivo, projetoId]);

  useEffect(() => {
    if (!projetoId) return;

    salvarLinhasCqt(projetoId, {
      esquerdo: estadoEsquerdo,
      direito: estadoDireito,
    });
  }, [estadoDireito, estadoEsquerdo, projetoId, salvarLinhasCqt]);

  const ladoAtivo = abaAtiva === "esquerdo" ? estadoEsquerdo : estadoDireito;
  const setLadoAtivo = abaAtiva === "esquerdo" ? setEstadoEsquerdo : setEstadoDireito;

  const mutation = useMutation({
    mutationFn: async () => {
      if (!projetoId) {
        throw new Error("Projeto ativo nao encontrado.");
      }

      const payload = montarPayloadCqt(ladoAtivo.trechos.map(sanitizeLinhaTrecho));
      const response = await api.post(`/projetos/${projetoId}/cqt`, payload);
      return response.data;
    },
  });

  const totalQueda = useMemo(() => mutation.data?.centro_carga?.queda_total_percent, [mutation.data]);
  const totalEsforcos = useMemo(
    () => ladoAtivo.trechos.reduce((acc, linha) => acc + toNumberOr(0, linha.esforco_dan || linha.corrente_a), 0),
    [ladoAtivo.trechos]
  );

  const atualizarLinha = (id, campo, valor) => {
    setLadoAtivo((atual) => ({
      ...atual,
      trechos: atual.trechos.map((linha) => (linha.id === id ? { ...linha, [campo]: valor } : linha)),
    }));
  };

  const adicionarLinha = () => {
    setLadoAtivo((atual) => ({
      ...atual,
      trechos: [...atual.trechos, criarLinhaInicial(atual.trechos.length + 1)],
    }));
  };

  const atualizarCabecalho = (campo, valor) => {
    setLadoAtivo((atual) => ({
      ...atual,
      cabecalho: {
        ...atual.cabecalho,
        [campo]: valor,
      },
    }));
  };

  if (!projetoId) {
    return (
      <section className="sec-panel" style={{ padding: "16px", color: "#9a3412", fontWeight: 700 }}>
        Nenhum projeto ativo encontrado. Crie ou selecione um projeto no Painel antes de calcular o CQT.
      </section>
    );
  }

  return (
    <section className="excel-container">
      <div className="excel-tabs legacy-sheet-tabs">
        <button
          type="button"
          className={`excel-tab ${abaAtiva === "esquerdo" ? "excel-tab-active" : ""}`}
          onClick={() => setAbaAtiva("esquerdo")}
        >
          LADO ESQUERDO
        </button>
        <button
          type="button"
          className={`excel-tab ${abaAtiva === "direito" ? "excel-tab-active" : ""}`}
          onClick={() => setAbaAtiva("direito")}
        >
          LADO DIREITO
        </button>
      </div>

      <LegacyExcelHeader
        dadosCabecalho={ladoAtivo.cabecalho}
        onChangeCampo={atualizarCabecalho}
        tituloAba={abaAtiva === "esquerdo" ? "QDT LADO 2 (ESQUERDO)" : "QDT LADO 1 (DIREITO)"}
      />

      <div className="excel-actions legacy-actions">
        <button type="button" className="excel-action-btn" onClick={adicionarLinha}>
          <PlusCircle size={14} style={{ marginRight: 6 }} />
          Inserir Trecho
        </button>
        <button type="button" className="excel-action-btn excel-action-btn-primary" onClick={() => mutation.mutate()} disabled={mutation.isPending}>
          <Calculator size={14} style={{ marginRight: 6 }} />
          Calcular
        </button>
      </div>

      <table className="excel-table legacy-main-grid">
        <thead>
          <tr>
            <th className="excel-th-dark" colSpan={4}>
              IDENTIFICACAO
            </th>
            <th className="excel-th-dark" colSpan={3}>
              DADOS GEOMETRICOS
            </th>
            <th className="excel-th-dark" colSpan={3}>
              ESFORCOS
            </th>
            <th className="excel-th-dark" colSpan={3}>
              QUEDA DE TENSAO
            </th>
          </tr>
          <tr>
            <th className="excel-th-light">TRECHO</th>
            <th className="excel-th-light">Nº DO POSTE</th>
            <th className="excel-th-light">TIPO DE TRECHO</th>
            <th className="excel-th-light">FIM</th>
            <th className="excel-th-light">VÃO (m)</th>
            <th className="excel-th-light">Nº FASES</th>
            <th className="excel-th-light">CONDUTOR</th>
            <th className="excel-th-light">CORRENTE (A)</th>
            <th className="excel-th-light">ESFORÇOS (daN)</th>
            <th className="excel-th-light">FP</th>
            <th className="excel-th-light">QUEDA TRECHO %</th>
            <th className="excel-th-light">QUEDA ACUM. %</th>
            <th className="excel-th-light">OBS.</th>
          </tr>
        </thead>
        <tbody>
          {ladoAtivo.trechos.map((linha, idx) => (
            <tr key={linha.id}>
              <td className="excel-td legacy-cell-center">{idx === ladoAtivo.trechos.length - 1 ? "RAMAL" : `P-${idx + 1}`}</td>
              <td className="excel-td">
                <input className="excel-input" value={linha.poste} onChange={(e) => atualizarLinha(linha.id, "poste", e.target.value)} />
              </td>
              <td className="excel-td legacy-cell-center">{idx === ladoAtivo.trechos.length - 1 ? "RL" : "Rede"}</td>
              <td className="excel-td legacy-cell-center">
                <select value={linha.fim_linha ?? "Nao"} onChange={(e) => atualizarLinha(linha.id, "fim_linha", e.target.value)}>
                  <option value="Nao">Nao</option>
                  <option value="Sim">Sim</option>
                </select>
              </td>
              <td className="excel-td">
                <input className="excel-input" value={linha.vao_m} onChange={(e) => atualizarLinha(linha.id, "vao_m", e.target.value)} />
              </td>
              <td className="excel-td legacy-cell-center">
                <input className="excel-input" value={linha.fases} onChange={(e) => atualizarLinha(linha.id, "fases", e.target.value)} />
              </td>
              <td className="excel-td">
                <input className="excel-input" value={linha.tipo_cabo} onChange={(e) => atualizarLinha(linha.id, "tipo_cabo", e.target.value)} />
              </td>
              <td className="excel-td">
                <input className="excel-input" value={linha.corrente_a} onChange={(e) => atualizarLinha(linha.id, "corrente_a", e.target.value)} />
              </td>
              <td className="excel-td">
                <input className="excel-input" value={linha.esforco_dan} onChange={(e) => atualizarLinha(linha.id, "esforco_dan", e.target.value)} />
              </td>
              <td className="excel-td legacy-cell-center">
                <input
                  className="excel-input"
                  value={ladoAtivo.cabecalho.fatorPotencia}
                  onChange={(e) => atualizarCabecalho("fatorPotencia", e.target.value)}
                />
              </td>
              <td className="excel-td">
                <input
                  className="excel-input"
                  value={linha.queda_tensao_trecho}
                  onChange={(e) => atualizarLinha(linha.id, "queda_tensao_trecho", e.target.value)}
                />
              </td>
              <td className="excel-td">
                <input
                  className="excel-input"
                  value={linha.queda_tensao_acumulada}
                  onChange={(e) => atualizarLinha(linha.id, "queda_tensao_acumulada", e.target.value)}
                />
              </td>
              <td className="excel-td">
                <input className="excel-input" value={linha.observacao ?? ""} onChange={(e) => atualizarLinha(linha.id, "observacao", e.target.value)} />
              </td>
            </tr>
          ))}
          {Array.from({ length: Math.max(0, 14 - ladoAtivo.trechos.length) }).map((_, idx) => (
            <tr key={`blank-${idx}`}>
              {Array.from({ length: 13 }).map((__, cellIdx) => (
                <td key={`${idx}-${cellIdx}`} className="excel-td legacy-empty-cell" />
              ))}
            </tr>
          ))}
        </tbody>
      </table>

      <div className="legacy-warning-strip">
        <span>{typeof totalQueda === "number" ? `${totalQueda.toFixed(2)} V` : "--,-- V"}</span>
        <span>Cuidado !!! A tensão no consumidor mais distante está abaixo do mínimo de 117 V estabelecido pela ANEEL !!!</span>
      </div>

      <div className="legacy-bottom-panels">
        <table className="excel-table legacy-mini-table">
          <thead>
            <tr>
              <th className="excel-th-dark" colSpan={5}>
                CARREGAMENTO DO TRAFO
              </th>
            </tr>
            <tr>
              <th className="excel-th-light">Nº do Poste</th>
              <th className="excel-th-light">Lado 1</th>
              <th className="excel-th-light">Carga</th>
              <th className="excel-th-light">Lado 2</th>
              <th className="excel-th-light">Carga</th>
            </tr>
          </thead>
          <tbody>
            {ladoAtivo.trechos.slice(0, 8).map((linha, idx) => (
              <tr key={`trafo-${linha.id}`}>
                <td className="excel-td legacy-cell-center">Poste {idx + 1}</td>
                <td className="excel-td">{toNumberOr(0, linha.corrente_a).toFixed(2)}</td>
                <td className="excel-td">{toNumberOr(0, linha.esforco_dan).toFixed(2)}</td>
                <td className="excel-td">{toNumberOr(0, linha.corrente_a).toFixed(2)}</td>
                <td className="excel-td">{toNumberOr(0, linha.esforco_dan).toFixed(2)}</td>
              </tr>
            ))}
          </tbody>
        </table>

        <table className="excel-table legacy-mini-table">
          <thead>
            <tr>
              <th className="excel-th-dark" colSpan={4}>
                PARÂMETROS DE QUEDA DE TENSÃO
              </th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <th className="excel-th-light">Corrente máxima</th>
              <td className="excel-td">{Math.max(...ladoAtivo.trechos.map((linha) => toNumberOr(0, linha.corrente_a))).toFixed(2)}</td>
              <th className="excel-th-light">Demanda máxima</th>
              <td className="excel-td">{totalEsforcos.toFixed(2)}</td>
            </tr>
            <tr>
              <th className="excel-th-light">Fator de temperatura</th>
              <td className="excel-td">1,20</td>
              <th className="excel-th-light">Demanda corrigida</th>
              <td className="excel-td">{(totalEsforcos * 1.2).toFixed(2)}</td>
            </tr>
            <tr>
              <th className="excel-th-light">QDT acumulada</th>
              <td className="excel-td">{typeof totalQueda === "number" ? totalQueda.toFixed(3) : "N/A"}</td>
              <th className="excel-th-light">Status trafo</th>
              <td className="excel-td">{mutation.data?.trafo_dentro_do_limite ? "Dentro" : "Aguardando"}</td>
            </tr>
            <tr>
              <th className="excel-th-light">QDT total no limite</th>
              <td className="excel-td">{mutation.data?.qdt_total_dentro_do_limite ? "Sim" : "Aguardando"}</td>
              <th className="excel-th-light">Observação</th>
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
      </div>

      {mutation.isError ? (
        <p className="result-box result-bad" style={{ marginBottom: 16 }}>
          Falha no calculo CQT: {mutation.error?.response?.data?.detail || mutation.error?.message || "erro desconhecido"}
        </p>
      ) : null}
    </section>
  );
}
