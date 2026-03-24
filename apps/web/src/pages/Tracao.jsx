import { useEffect, useMemo, useRef, useState } from "react";

import { useMutation } from "@tanstack/react-query";

import "../styles/tracaoLegacy.css";

import { LegacyDiagramaPoste } from "../components/tracao/LegacyDiagramaPoste";
import { LegacyTabelaCarga } from "../components/tracao/LegacyTabelaCarga";
import { LegacyTracaoGrid } from "../components/tracao/LegacyTracaoGrid";
import {
  STATUS_VAZIO,
  TABELA_CARGAS_POSTE,
  atualizarCampoPoste,
  atualizarTravessiaSecao,
  criarEstadoInicialTracao,
  mapearStatusTracao,
  montarExecucaoTracao,
  normalizarEstadoTracao,
  resumoTracao,
} from "../components/tracao/legacyTracaoModel";
import api from "../lib/api";
import { useGridStore } from "../store/useGridStore";
import { useProjectStore } from "../store/useProjectStore";

export function Tracao() {
  const { projetoAtivo } = useProjectStore();
  const { obterEstadoTracaoVisual, salvarEstadoTracaoVisual } = useGridStore();
  const [estadoVisual, setEstadoVisual] = useState(criarEstadoInicialTracao);
  const [statusPorSecao, setStatusPorSecao] = useState(STATUS_VAZIO);
  const fileInputRef = useRef(null);
  const projetoId = projetoAtivo?.id || null;

  useEffect(() => {
    if (!projetoId) return;
    setEstadoVisual(normalizarEstadoTracao(obterEstadoTracaoVisual(projetoId, criarEstadoInicialTracao)));
  }, [obterEstadoTracaoVisual, projetoId]);

  useEffect(() => {
    if (!projetoId) return;
    salvarEstadoTracaoVisual(projetoId, estadoVisual);
  }, [estadoVisual, projetoId, salvarEstadoTracaoVisual]);

  const mutation = useMutation({
    mutationFn: async () => {
      if (!projetoId) throw new Error("Projeto ativo nao encontrado.");
      const { postosEntrada } = montarExecucaoTracao(estadoVisual);
      if (!postosEntrada.length) throw new Error("Preencha pelo menos uma travessia antes de calcular.");
      const response = await api.post(`/projetos/${projetoId}/tracao`, { postes: postosEntrada });
      return { data: response.data, postosEntrada };
    },
    onSuccess: ({ data, postosEntrada }) => setStatusPorSecao(mapearStatusTracao(estadoVisual, postosEntrada, data.resultados)),
  });

  const importMutation = useMutation({
    mutationFn: async (arquivo) => {
      const formData = new FormData();
      formData.append("file", arquivo);
      const response = await api.post("/tracao/importar-excel", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      return response.data;
    },
    onSuccess: (estadoImportado) => {
      setEstadoVisual(normalizarEstadoTracao(estadoImportado));
      setStatusPorSecao(STATUS_VAZIO);
    },
  });

  const abrirImportador = () => {
    fileInputRef.current?.click();
  };

  const aoSelecionarArquivo = (event) => {
    const arquivo = event.target.files?.[0];
    if (!arquivo) return;
    importMutation.mutate(arquivo);
    event.target.value = "";
  };

  const resumo = useMemo(() => resumoTracao(mutation.data?.data?.resultados || []), [mutation.data]);

  if (!projetoId) {
    return (
      <section className="sec-panel" style={{ padding: "16px", color: "#9a3412", fontWeight: 700 }}>
        Nenhum projeto ativo encontrado. Crie ou selecione um projeto no Painel antes de calcular a Tracao.
      </section>
    );
  }

  return (
    <section className="excel-container legacy-tracao-page">
      <table className="excel-table legacy-tracao-header-table">
        <tbody>
          <tr>
            <th className="excel-th-light">Tipo do Poste</th>
            <td className="excel-td"><input className="excel-input" value={estadoVisual.dadosPoste.tipoPoste} onChange={(e) => setEstadoVisual((p) => atualizarCampoPoste(p, "tipoPoste", e.target.value))} /></td>
            <th className="excel-th-light">Esforco Nominal (daN)</th>
            <td className="excel-td"><input className="excel-input" value={estadoVisual.dadosPoste.modeloPoste} onChange={(e) => setEstadoVisual((p) => atualizarCampoPoste(p, "modeloPoste", e.target.value))} /></td>
            <th className="excel-th-light">Coordenadas</th>
            <td className="excel-td"><input className="excel-input" value={estadoVisual.dadosPoste.coordenadas} onChange={(e) => setEstadoVisual((p) => atualizarCampoPoste(p, "coordenadas", e.target.value))} /></td>
            <td className="excel-td legacy-cell-center"><button type="button" className="excel-action-btn" onClick={abrirImportador} disabled={importMutation.isPending}>Importar Planilha Legada</button></td>
            <td className="excel-td legacy-cell-center"><button type="button" className="excel-action-btn excel-action-btn-primary" onClick={() => mutation.mutate()} disabled={mutation.isPending}>APAGA/CALCULA</button></td>
          </tr>
          <tr><td className="legacy-tracao-total" colSpan={8}>TRAÇÃO TOTAL: {resumo.APROVADO + resumo.ALERTA + resumo.REPROVADO} daN</td></tr>
        </tbody>
      </table>
      <input ref={fileInputRef} type="file" accept=".xlsm,.xlsx" style={{ display: "none" }} onChange={aoSelecionarArquivo} />

      <LegacyTracaoGrid secoes={estadoVisual.secoes} statusPorSecao={statusPorSecao} onChangeTravessia={(secao, idx, campo, valor) => setEstadoVisual((p) => atualizarTravessiaSecao(p, secao, idx, campo, valor))} />

      <div className="legacy-tracao-side">
        <LegacyDiagramaPoste />
        <LegacyTabelaCarga dados={TABELA_CARGAS_POSTE} />
      </div>

      {mutation.isError ? <p className="result-box result-bad">Falha no calculo de Tracao: {mutation.error?.response?.data?.detail || mutation.error?.message || "erro desconhecido"}</p> : null}
      {importMutation.isError ? <p className="result-box result-bad">Falha na importacao: {importMutation.error?.response?.data?.detail || importMutation.error?.message || "erro desconhecido"}</p> : null}
    </section>
  );
}
