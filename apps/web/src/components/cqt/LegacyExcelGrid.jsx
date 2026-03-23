import { Calculator, PlusCircle } from "lucide-react";

import { toNumberOr } from "./legacyCqtModel";

export function LegacyExcelGrid({
  dados,
  totalQueda,
  totalEsforcos,
  resultado,
  onLinhaChange,
  onCabecalhoChange,
  onAddLinha,
  onCalcular,
  isCalculando,
}) {
  const trechos = dados?.trechos || [];
  const cabecalho = dados?.cabecalho || {};

  return (
    <>
      <div className="excel-actions legacy-actions">
        <button type="button" className="excel-action-btn" onClick={onAddLinha}>
          <PlusCircle size={14} style={{ marginRight: 6 }} />
          Inserir Trecho
        </button>
        <button
          type="button"
          className="excel-action-btn excel-action-btn-primary"
          onClick={onCalcular}
          disabled={isCalculando}
        >
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
          {trechos.map((linha, idx) => (
            <tr key={linha.id}>
              <td className="excel-td legacy-cell-center">{idx === trechos.length - 1 ? "RAMAL" : `P-${idx + 1}`}</td>
              <td className="excel-td">
                <input className="excel-input" value={linha.poste} onChange={(e) => onLinhaChange(linha.id, "poste", e.target.value)} />
              </td>
              <td className="excel-td legacy-cell-center">{idx === trechos.length - 1 ? "RL" : "Rede"}</td>
              <td className="excel-td legacy-cell-center">
                <select value={linha.fim_linha ?? "Nao"} onChange={(e) => onLinhaChange(linha.id, "fim_linha", e.target.value)}>
                  <option value="Nao">Nao</option>
                  <option value="Sim">Sim</option>
                </select>
              </td>
              <td className="excel-td">
                <input className="excel-input" value={linha.vao_m} onChange={(e) => onLinhaChange(linha.id, "vao_m", e.target.value)} />
              </td>
              <td className="excel-td legacy-cell-center">
                <input className="excel-input" value={linha.fases} onChange={(e) => onLinhaChange(linha.id, "fases", e.target.value)} />
              </td>
              <td className="excel-td">
                <input className="excel-input" value={linha.tipo_cabo} onChange={(e) => onLinhaChange(linha.id, "tipo_cabo", e.target.value)} />
              </td>
              <td className="excel-td">
                <input className="excel-input" value={linha.corrente_a} onChange={(e) => onLinhaChange(linha.id, "corrente_a", e.target.value)} />
              </td>
              <td className="excel-td">
                <input className="excel-input" value={linha.esforco_dan} onChange={(e) => onLinhaChange(linha.id, "esforco_dan", e.target.value)} />
              </td>
              <td className="excel-td legacy-cell-center">
                <input
                  className="excel-input"
                  value={cabecalho.fatorPotencia || ""}
                  onChange={(e) => onCabecalhoChange("fatorPotencia", e.target.value)}
                />
              </td>
              <td className="excel-td">
                <input
                  className="excel-input"
                  value={linha.queda_tensao_trecho || ""}
                  onChange={(e) => onLinhaChange(linha.id, "queda_tensao_trecho", e.target.value)}
                />
              </td>
              <td className="excel-td">
                <input
                  className="excel-input"
                  value={linha.queda_tensao_acumulada || ""}
                  onChange={(e) => onLinhaChange(linha.id, "queda_tensao_acumulada", e.target.value)}
                />
              </td>
              <td className="excel-td">
                <input className="excel-input" value={linha.observacao || ""} onChange={(e) => onLinhaChange(linha.id, "observacao", e.target.value)} />
              </td>
            </tr>
          ))}
          {Array.from({ length: Math.max(0, 14 - trechos.length) }).map((_, idx) => (
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
            {trechos.slice(0, 8).map((linha, idx) => (
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
              <td className="excel-td">{Math.max(...trechos.map((linha) => toNumberOr(0, linha.corrente_a))).toFixed(2)}</td>
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
              <td className="excel-td">{resultado?.trafo_dentro_do_limite ? "Dentro" : "Aguardando"}</td>
            </tr>
            <tr>
              <th className="excel-th-light">QDT total no limite</th>
              <td className="excel-td">{resultado?.qdt_total_dentro_do_limite ? "Sim" : "Aguardando"}</td>
              <th className="excel-th-light">Observação</th>
              <td className="excel-td">
                <input
                  className="excel-input"
                  value={cabecalho.observacoes || ""}
                  onChange={(e) => onCabecalhoChange("observacoes", e.target.value)}
                />
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </>
  );
}
