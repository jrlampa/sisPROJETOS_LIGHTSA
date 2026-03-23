import { useEffect, useMemo, useState } from "react";

import { useMutation } from "@tanstack/react-query";

import { LegacyDiagramaPoste } from "../components/tracao/LegacyDiagramaPoste";
import { LegacySecaoNivel } from "../components/tracao/LegacySecaoNivel";
import { LegacyTabelaCarga } from "../components/tracao/LegacyTabelaCarga";
import {
  CAMPOS_BT,
  CAMPOS_BTZ,
  CAMPOS_MT,
  CAMPOS_RAL,
  TRAVESSIA_BTZ_VAZIA,
  TRAVESSIA_MT_VAZIA,
  TRAVESSIA_RAL_VAZIA,
  createTravessiasVazias,
  updateTravessia,
} from "../components/tracao/legacyFormConfig";
import api from "../lib/api";
import { useGridStore } from "../store/useGridStore";
import { useProjectStore } from "../store/useProjectStore";

const TABELA_CARGAS_POSTE = [
  { alpha: "-", R300: 300, R600: 600 },
  { alpha: 0, R300: 300, R600: 600 },
  { alpha: 5, R300: 299, R600: 598 },
  { alpha: 10, R300: 288, R600: 577 },
  { alpha: 15, R300: 278, R600: 556 },
  { alpha: 20, R300: 268, R600: 536 },
  { alpha: 25, R300: 259, R600: 517 },
  { alpha: 30, R300: 250, R600: 499 },
  { alpha: 40, R300: 232, R600: 464 },
  { alpha: 50, R300: 216, R600: 432 },
  { alpha: 60, R300: 201, R600: 402 },
  { alpha: 70, R300: 187, R600: 374 },
  { alpha: 80, R300: 174, R600: 348 },
  { alpha: 90, R300: 150, R600: 300 },
];

function criarEstadoInicial() {
  return {
    tipoPoste: "",
    modeloPoste: "",
    secoes: {
      mt1: createTravessiasVazias(TRAVESSIA_MT_VAZIA),
      mt2: createTravessiasVazias(TRAVESSIA_MT_VAZIA),
      bt: createTravessiasVazias(TRAVESSIA_BTZ_VAZIA),
      ral: createTravessiasVazias(TRAVESSIA_RAL_VAZIA),
    },
  };
}

function toNumberOr(defaultValue, value) {
  const number = Number(value);
  return Number.isFinite(number) ? number : defaultValue;
}

function secaoToPayload(sectionKey, travessias, resistenciaNominal) {
  return travessias
    .map((travessia, idx) => ({ travessia, idx }))
    .filter(({ travessia }) =>
      ["tipoCabo", "vao", "flecha", "angulo", "qtdCabos", "qtdLigacoes"].some((key) => String(travessia[key] || "").trim() !== "")
    )
    .map(({ travessia, idx }) => ({
      codigo: `${sectionKey.toUpperCase()}-T${idx + 1}`,
      resistencia_nominal_daN: resistenciaNominal,
      vaos: [
        {
          comprimento_m: toNumberOr(10, travessia.vao),
          tipo_cabo: travessia.tipoCabo || "CAA 70mm2",
          tracao_daN: toNumberOr(100, travessia.flecha || travessia.qtdCabos || travessia.qtdLigacoes),
          azimute_graus: toNumberOr(0, travessia.angulo) % 360,
        },
      ],
    }));
}

function mapResultadosPorSecao(indexMap, resultados) {
  const bySection = { mt1: ["-", "-", "-", "-"], mt2: ["-", "-", "-", "-"], bt: ["-", "-", "-", "-"], ral: ["-", "-", "-", "-"] };
  resultados.forEach((res, i) => {
    const pos = indexMap[i];
    if (!pos) return;
    bySection[pos.secao][pos.idx] = res.estado_mecanico;
  });
  return bySection;
}

export function Tracao() {
  const { projetoAtivo } = useProjectStore();
  const { obterEstadoTracaoVisual, salvarEstadoTracaoVisual } = useGridStore();

  const [estadoVisual, setEstadoVisual] = useState(criarEstadoInicial);
  const [statusPorSecao, setStatusPorSecao] = useState({ mt1: ["-", "-", "-", "-"], mt2: ["-", "-", "-", "-"], bt: ["-", "-", "-", "-"], ral: ["-", "-", "-", "-"] });
  const projetoId = projetoAtivo?.id || null;

  useEffect(() => {
    if (!projetoId) return;
    const estado = obterEstadoTracaoVisual(projetoId, criarEstadoInicial);
    setEstadoVisual(estado);
  }, [obterEstadoTracaoVisual, projetoId]);

  useEffect(() => {
    if (!projetoId) return;
    salvarEstadoTracaoVisual(projetoId, estadoVisual);
  }, [estadoVisual, projetoId, salvarEstadoTracaoVisual]);

  const atualizarTravessia = (secao, idx, campo, valor) => {
    setEstadoVisual((prev) => ({
      ...prev,
      secoes: {
        ...prev.secoes,
        [secao]: updateTravessia(prev.secoes[secao], idx, campo, valor),
      },
    }));
  };

  const mutation = useMutation({
    mutationFn: async () => {
      if (!projetoId) throw new Error("Projeto ativo nao encontrado.");

      const resistenciaNominal = toNumberOr(300, estadoVisual.modeloPoste);
      const merged = [
        ...secaoToPayload("mt1", estadoVisual.secoes.mt1, resistenciaNominal),
        ...secaoToPayload("mt2", estadoVisual.secoes.mt2, resistenciaNominal),
        ...secaoToPayload("bt", estadoVisual.secoes.bt, resistenciaNominal),
        ...secaoToPayload("ral", estadoVisual.secoes.ral, resistenciaNominal),
      ];

      if (merged.length === 0) {
        throw new Error("Preencha pelo menos uma travessia antes de calcular.");
      }

      const response = await api.post(`/projetos/${projetoId}/tracao`, { postes: merged });
      return { data: response.data, postosEntrada: merged };
    },
    onSuccess: ({ data, postosEntrada }) => {
      const indexMap = [];
      let k = 0;
      ["mt1", "mt2", "bt", "ral"].forEach((secao) => {
        estadoVisual.secoes[secao].forEach((travessia, idx) => {
          const temValor = ["tipoCabo", "vao", "flecha", "angulo", "qtdCabos", "qtdLigacoes"].some(
            (key) => String(travessia[key] || "").trim() !== ""
          );
          if (temValor && postosEntrada[k]) {
            indexMap.push({ secao, idx });
            k += 1;
          }
        });
      });
      setStatusPorSecao(mapResultadosPorSecao(indexMap, data.resultados || []));
    },
  });

  const resumo = useMemo(() => {
    const resultados = mutation.data?.data?.resultados || [];
    const totais = { APROVADO: 0, ALERTA: 0, REPROVADO: 0 };
    resultados.forEach((item) => {
      const key = item.estado_mecanico;
      if (totais[key] !== undefined) totais[key] += 1;
    });
    return totais;
  }, [mutation.data]);

  if (!projetoId) {
    return (
      <section className="sec-panel" style={{ padding: "16px", color: "#9a3412", fontWeight: 700 }}>
        Nenhum projeto ativo encontrado. Crie ou selecione um projeto no Dashboard antes de calcular a Tracao.
      </section>
    );
  }

  return (
    <section className="page-wrap" style={{ padding: "8px" }}>
      <div className="calc-layout">
        <div className="calc-main-column">
          <div className="sec-panel" style={{ marginBottom: 8 }}>
            <div className="sec-title">Calculo de Tracao</div>
            <div style={{ padding: 8 }}>
              <div style={{ display: "grid", gridTemplateColumns: "130px 1fr", gap: 6, alignItems: "center" }}>
                <span className="poste-lbl" style={{ fontWeight: 700 }}>Tipo do Poste</span>
                <input
                  className="xcell poste-select"
                  value={estadoVisual.tipoPoste}
                  onChange={(e) => setEstadoVisual((prev) => ({ ...prev, tipoPoste: e.target.value }))}
                />
                <span className="poste-lbl" style={{ fontWeight: 700 }}>Modelo do Poste (daN)</span>
                <input
                  className="xcell poste-select"
                  value={estadoVisual.modeloPoste}
                  onChange={(e) => setEstadoVisual((prev) => ({ ...prev, modeloPoste: e.target.value }))}
                  placeholder="Ex: 300"
                />
              </div>
              <div style={{ marginTop: 8, display: "flex", gap: 8, flexWrap: "wrap" }}>
                <button type="button" className="btn-primary" onClick={() => mutation.mutate()} disabled={mutation.isPending}>
                  Calcular Tracao
                </button>
              </div>
            </div>
          </div>

          <div className="tracao-total-box" style={{ marginBottom: 8 }}>
            APROVADO: {resumo.APROVADO} | ALERTA: {resumo.ALERTA} | REPROVADO: {resumo.REPROVADO}
          </div>

          <LegacySecaoNivel
            titulo="MT - 1o Nivel"
            labelResultado="TRACAO MT 1o NIVEL"
            travessias={estadoVisual.secoes.mt1}
            onChangeTravessia={(idx, campo, valor) => atualizarTravessia("mt1", idx, campo, valor)}
            campos={CAMPOS_MT}
            statusPorTravessia={statusPorSecao.mt1}
          />

          <LegacySecaoNivel
            titulo="MT - 2o Nivel"
            labelResultado="TRACAO MT 2o NIVEL"
            travessias={estadoVisual.secoes.mt2}
            onChangeTravessia={(idx, campo, valor) => atualizarTravessia("mt2", idx, campo, valor)}
            campos={CAMPOS_MT}
            statusPorTravessia={statusPorSecao.mt2}
          />

          <LegacySecaoNivel
            titulo="BT - Zona"
            labelResultado="TRACAO BT ZONA"
            travessias={estadoVisual.secoes.bt}
            onChangeTravessia={(idx, campo, valor) => atualizarTravessia("bt", idx, campo, valor)}
            campos={CAMPOS_BTZ}
            statusPorTravessia={statusPorSecao.bt}
            nota="(*) Preencher de acordo com levantamento de campo"
          />

          <LegacySecaoNivel
            titulo="Ramal"
            labelResultado="TRACAO RAMAL"
            travessias={estadoVisual.secoes.ral}
            onChangeTravessia={(idx, campo, valor) => atualizarTravessia("ral", idx, campo, valor)}
            campos={CAMPOS_RAL}
            statusPorTravessia={statusPorSecao.ral}
          />

          {mutation.isError ? (
            <p className="result-box result-bad" style={{ fontWeight: 700 }}>
              Falha no calculo de Tracao: {mutation.error?.response?.data?.detail || mutation.error?.message || "erro desconhecido"}
            </p>
          ) : null}
        </div>

        <div className="calc-side-column" style={{ width: 220 }}>
          <div className="sec-panel" style={{ width: "100%", marginBottom: 10 }}>
            <div className="sec-title">Resumo Visual</div>
            <div style={{ padding: 8, fontSize: 10, lineHeight: 1.4 }}>
              Estados mecanicos refletidos diretamente da API apos o calculo.
            </div>
          </div>
          <LegacyDiagramaPoste />
          <LegacyTabelaCarga dados={TABELA_CARGAS_POSTE} />
        </div>
      </div>
    </section>
  );
}
