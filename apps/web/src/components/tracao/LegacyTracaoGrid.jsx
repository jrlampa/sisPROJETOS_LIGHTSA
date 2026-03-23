import { Fragment } from "react";

import { SECOES_LEGACY, momentoX, momentoY, toNumberOr } from "./legacyTracaoModel";

function classeStatus(estado) {
  if (estado === "APROVADO") return "result-ok";
  if (estado === "ALERTA") return "result-warn";
  if (estado === "REPROVADO") return "result-bad";
  return "";
}

function valorCampoTravessia(secaoKey, linha, campo) {
  if (campo === "tipoRede") return linha?.tipoRede || (secaoKey === "bt" ? "BT" : "MT");
  if (campo === "tipoCabo") return linha?.tipoCabo || "";
  if (campo === "tracao") return linha?.flecha || linha?.qtdCabos || linha?.qtdLigacoes || "";
  return linha?.[campo] ?? "";
}

export function LegacyTracaoGrid({ secoes, statusPorSecao, onChangeTravessia }) {
  return (
    <table className="excel-table legacy-tracao-grid">
      <tbody>
        {SECOES_LEGACY.map((secao) => {
          const linhas = secoes[secao.key] || [];
          const status = statusPorSecao[secao.key] || ["-", "-", "-", "-"];
          const somaTracao = linhas.reduce((acc, linha) => acc + toNumberOr(0, valorCampoTravessia(secao.key, linha, "tracao")), 0);
          const anguloMedio = linhas.length ? linhas.reduce((acc, linha) => acc + toNumberOr(0, linha?.angulo), 0) / linhas.length : 0;

          return (
            <Fragment key={secao.key}>
              <tr key={`${secao.key}-lvl`}>
                <th className="excel-th-dark legacy-system-header" colSpan={13}>{secao.titulo}</th>
              </tr>
              <tr key={`${secao.key}-hdr`}>
                <th className="excel-th-light">Trav.</th>
                <th className="excel-th-light">Tipo de Rede</th>
                <th className="excel-th-light">Tipo de Cabo</th>
                <th className="excel-th-light">Vão (m)</th>
                <th className="excel-th-light">Flecha/Tração</th>
                <th className="excel-th-light">Ângulo (°)</th>
                <th className="excel-th-light">Alt. Poste</th>
                <th className="excel-th-light">Alt. Ancoragem</th>
                <th className="excel-th-light">Qtd. Cabos</th>
                <th className="excel-th-light">Qtd. Ligações</th>
                <th className="excel-th-light">Momento X</th>
                <th className="excel-th-light">Momento Y</th>
                <th className="excel-th-light">Status</th>
              </tr>
              {linhas.map((linha, idx) => {
                const mx = momentoX(linha);
                const my = momentoY(linha);
                const st = status[idx] || "-";

                return (
                  <tr key={`${secao.key}-${idx}`}>
                    <td className="excel-td legacy-cell-center">T{idx + 1}</td>
                    <td className="excel-td">
                      <input className="excel-input" value={valorCampoTravessia(secao.key, linha, "tipoRede")} onChange={(e) => onChangeTravessia(secao.key, idx, "tipoRede", e.target.value)} />
                    </td>
                    <td className="excel-td">
                      <input className="excel-input" value={valorCampoTravessia(secao.key, linha, "tipoCabo")} onChange={(e) => onChangeTravessia(secao.key, idx, "tipoCabo", e.target.value)} />
                    </td>
                    <td className="excel-td">
                      <input className="excel-input" value={valorCampoTravessia(secao.key, linha, "vao")} onChange={(e) => onChangeTravessia(secao.key, idx, "vao", e.target.value)} />
                    </td>
                    <td className="excel-td">
                      <input className="excel-input" value={valorCampoTravessia(secao.key, linha, "tracao")} onChange={(e) => onChangeTravessia(secao.key, idx, "flecha", e.target.value)} />
                    </td>
                    <td className="excel-td">
                      <input className="excel-input" value={valorCampoTravessia(secao.key, linha, "angulo")} onChange={(e) => onChangeTravessia(secao.key, idx, "angulo", e.target.value)} />
                    </td>
                    <td className="excel-td">
                      <input className="excel-input" value={valorCampoTravessia(secao.key, linha, "alturaPoste")} onChange={(e) => onChangeTravessia(secao.key, idx, "alturaPoste", e.target.value)} />
                    </td>
                    <td className="excel-td">
                      <input className="excel-input" value={valorCampoTravessia(secao.key, linha, "alturaAncoragem")} onChange={(e) => onChangeTravessia(secao.key, idx, "alturaAncoragem", e.target.value)} />
                    </td>
                    <td className="excel-td">
                      <input className="excel-input" value={linha?.qtdCabos ?? ""} onChange={(e) => onChangeTravessia(secao.key, idx, "qtdCabos", e.target.value)} />
                    </td>
                    <td className="excel-td">
                      <input className="excel-input" value={linha?.qtdLigacoes ?? ""} onChange={(e) => onChangeTravessia(secao.key, idx, "qtdLigacoes", e.target.value)} />
                    </td>
                    <td className="excel-td legacy-cell-right">{mx.toFixed(2)}</td>
                    <td className="excel-td legacy-cell-right">{my.toFixed(2)}</td>
                    <td className={`excel-td legacy-cell-center ${classeStatus(st)}`}>{st}</td>
                  </tr>
                );
              })}
              <tr key={`${secao.key}-sum`}>
                <th className="excel-th-light" colSpan={4}>SOMATÓRIOS / RESULTANTES</th>
                <td className="excel-td legacy-cell-right">{somaTracao.toFixed(2)}</td>
                <td className="excel-td legacy-cell-right">{anguloMedio.toFixed(2)}</td>
                <td className="excel-td" colSpan={2}>-</td>
                <td className="excel-td" colSpan={2}>-</td>
                <td className="excel-td legacy-cell-right">{linhas.reduce((acc, linha) => acc + momentoX(linha), 0).toFixed(2)}</td>
                <td className="excel-td legacy-cell-right">{linhas.reduce((acc, linha) => acc + momentoY(linha), 0).toFixed(2)}</td>
                <td className="excel-td legacy-cell-center">{status.join(" / ")}</td>
              </tr>
            </Fragment>
          );
        })}
      </tbody>
    </table>
  );
}
