export function LegacyExcelHeader({ dadosCabecalho, onChangeCampo }) {
  return (
    <div className="legacy-header-wrap">
      <table className="excel-table legacy-header-title">
        <tbody>
          <tr>
            <td className="legacy-header-company">Light S.E.S.A. DDE - Engenharia da Distribuição</td>
          </tr>
        </tbody>
      </table>

      <table className="excel-table legacy-header-grid">
        <tbody>
          <tr>
            <th className="excel-th-dark" colSpan={3}>
              TRAFO ESTAÇÃO "AT-MT"
            </th>
            <td colSpan={1} />
            <th className="excel-th-dark" colSpan={2}>
              CIRCUITO DE M.T.
            </th>
          </tr>
          <tr>
            <th className="excel-th-light">Potência</th>
            <th className="excel-th-light">Impedância</th>
            <th className="excel-th-light">Tensão</th>
            <td />
            <th className="excel-th-light">Circuito</th>
            <th className="excel-th-light">Lance</th>
          </tr>
          <tr>
            <th className="excel-th-light">[ MVA ]</th>
            <th className="excel-th-light">Z %</th>
            <th className="excel-th-light">[ kV ]</th>
            <td />
            <th className="excel-th-light">Carregamento</th>
            <td />
          </tr>
          <tr>
            <td className="excel-td">
              <input
                className="excel-input"
                value={dadosCabecalho.trafoMva}
                onChange={(e) => onChangeCampo("trafoMva", e.target.value)}
                placeholder="40"
              />
            </td>
            <td className="excel-td">
              <input
                className="excel-input"
                value={dadosCabecalho.impedanciaZ}
                onChange={(e) => onChangeCampo("impedanciaZ", e.target.value)}
                placeholder="20"
              />
            </td>
            <td className="excel-td">
              <input
                className="excel-input"
                value={dadosCabecalho.tensaoKv}
                onChange={(e) => onChangeCampo("tensaoKv", e.target.value)}
                placeholder="13.2"
              />
            </td>
            <td />
            <td className="excel-td">
              <input
                className="excel-input"
                value={dadosCabecalho.circuito}
                onChange={(e) => onChangeCampo("circuito", e.target.value)}
                placeholder="53 SC - MT - A"
              />
            </td>
            <td className="excel-td">
              <input
                className="excel-input"
                value={dadosCabecalho.lanceCqt}
                onChange={(e) => onChangeCampo("lanceCqt", e.target.value)}
                placeholder="2"
              />
            </td>
          </tr>
          <tr style={{ height: "6px" }}>
            <td colSpan={6} />
          </tr>
          <tr>
            <th className="excel-th-light">Referência</th>
            <td className="excel-td" colSpan={2}>
              <input
                className="excel-input"
                value={dadosCabecalho.dataRef}
                onChange={(e) => onChangeCampo("dataRef", e.target.value)}
                placeholder="2015-12-30"
              />
            </td>
            <td />
            <th className="excel-th-light">Atualização</th>
            <td className="excel-td">
              <input
                className="excel-input"
                value={dadosCabecalho.dataAtualizacao}
                onChange={(e) => onChangeCampo("dataAtualizacao", e.target.value)}
                placeholder="2026-03-17"
              />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}
