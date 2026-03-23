import { useEffect, useMemo, useState } from "react";

import { useMutation } from "@tanstack/react-query";

import { montarPayloadCqt } from "../adapters/cqtAdapter";
import { LegacyExcelGrid } from "../components/cqt/LegacyExcelGrid";
import { LegacyExcelHeader } from "../components/cqt/LegacyExcelHeader";
import { criarEstadoLadoInicial, criarLinhaInicial, normalizarEstadoLado, sanitizeLinhaTrecho, toNumberOr } from "../components/cqt/legacyCqtModel";
import api from "../lib/api";
import { useGridStore } from "../store/useGridStore";
import { useProjectStore } from "../store/useProjectStore";

export function CQT() {
  const { projetoAtivo } = useProjectStore();
  const { obterLinhasCqt, salvarLinhasCqt } = useGridStore();
  const [abaAtiva, setAbaAtiva] = useState("esquerdo");
  const [estadoEsquerdo, setEstadoEsquerdo] = useState(() => criarEstadoLadoInicial(projetoAtivo));
  const [estadoDireito, setEstadoDireito] = useState(() => criarEstadoLadoInicial(projetoAtivo));
  const projetoId = projetoAtivo?.id || null;

  useEffect(() => {
    if (!projetoId) return;
    const estadoSalvo = obterLinhasCqt(projetoId, () => ({ esquerdo: criarEstadoLadoInicial(projetoAtivo), direito: criarEstadoLadoInicial(projetoAtivo) }));
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
    salvarLinhasCqt(projetoId, { esquerdo: estadoEsquerdo, direito: estadoDireito });
  }, [estadoDireito, estadoEsquerdo, projetoId, salvarLinhasCqt]);

  const ladoAtivo = abaAtiva === "esquerdo" ? estadoEsquerdo : estadoDireito;
  const setLadoAtivo = abaAtiva === "esquerdo" ? setEstadoEsquerdo : setEstadoDireito;
  const atualizarLinha = (id, campo, valor) => setLadoAtivo((atual) => ({ ...atual, trechos: atual.trechos.map((linha) => (linha.id === id ? { ...linha, [campo]: valor } : linha)) }));
  const atualizarCabecalho = (campo, valor) => setLadoAtivo((atual) => ({ ...atual, cabecalho: { ...atual.cabecalho, [campo]: valor } }));
  const adicionarLinha = () => setLadoAtivo((atual) => ({ ...atual, trechos: [...atual.trechos, criarLinhaInicial(atual.trechos.length + 1)] }));

  const mutation = useMutation({
    mutationFn: async () => {
      if (!projetoId) throw new Error("Projeto ativo nao encontrado.");
      const payload = montarPayloadCqt(ladoAtivo.trechos.map(sanitizeLinhaTrecho));
      const response = await api.post(`/projetos/${projetoId}/cqt`, payload);
      return response.data;
    },
  });

  const totalQueda = useMemo(() => mutation.data?.centro_carga?.queda_total_percent, [mutation.data]);
  const totalEsforcos = useMemo(() => ladoAtivo.trechos.reduce((acc, linha) => acc + toNumberOr(0, linha.esforco_dan || linha.corrente_a), 0), [ladoAtivo.trechos]);

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
        <button type="button" className={`excel-tab ${abaAtiva === "esquerdo" ? "excel-tab-active" : ""}`} onClick={() => setAbaAtiva("esquerdo")}>LADO ESQUERDO</button>
        <button type="button" className={`excel-tab ${abaAtiva === "direito" ? "excel-tab-active" : ""}`} onClick={() => setAbaAtiva("direito")}>LADO DIREITO</button>
      </div>
      <LegacyExcelHeader dadosCabecalho={ladoAtivo.cabecalho} onChangeCampo={atualizarCabecalho} tituloAba={abaAtiva === "esquerdo" ? "QDT LADO 2 (ESQUERDO)" : "QDT LADO 1 (DIREITO)"} />
      <LegacyExcelGrid
        dados={ladoAtivo}
        totalQueda={totalQueda}
        totalEsforcos={totalEsforcos}
        resultado={mutation.data}
        onLinhaChange={atualizarLinha}
        onCabecalhoChange={atualizarCabecalho}
        onAddLinha={adicionarLinha}
        onCalcular={() => mutation.mutate()}
        isCalculando={mutation.isPending}
      />
      {mutation.isError ? (
        <p className="result-box result-bad" style={{ marginBottom: 16 }}>
          Falha no calculo CQT: {mutation.error?.response?.data?.detail || mutation.error?.message || "erro desconhecido"}
        </p>
      ) : null}
    </section>
  );
}
