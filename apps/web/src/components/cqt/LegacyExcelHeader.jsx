export function LegacyExcelHeader({ dadosCabecalho, onChangeCampo, tituloAba }) {
  return (
    <div className="legacy-header-wrap">
      <table className="excel-table legacy-title-table">
        <tbody>
          <tr>
            <td className="legacy-brand-left">LIGHT - SERVIÇOS DE ELETRICIDADE S.A.</td>
            <td className="legacy-title-main">CÁLCULO DA QUEDA DE TENSÃO E ESFORÇOS MECÂNICOS</td>
            <td className="legacy-brand-right">{tituloAba}</td>
          </tr>
        </tbody>
      </table>

      <table className="excel-table legacy-header-grid">
        <thead>
          <tr>
            <th className="excel-th-dark" colSpan={8}>
              DADOS DO PROJETO
            </th>
            <th className="excel-th-dark" colSpan={8}>
              CARACTERÍSTICAS DA REDE
            </th>
          </tr>
        </thead>
        <tbody>
          <tr>
            <th className="excel-th-light legacy-row-label">Projeto</th>
            <td className="excel-td" colSpan={3}>
              <input
                className="excel-input"
                value={dadosCabecalho.nomeProjeto}
                onChange={(e) => onChangeCampo("nomeProjeto", e.target.value)}
              />
            </td>
            <th className="excel-th-light legacy-row-label">Projetista</th>
            <td className="excel-td" colSpan={3}>
              <input
                className="excel-input"
                value={dadosCabecalho.projetista}
                onChange={(e) => onChangeCampo("projetista", e.target.value)}
              />
            </td>
            <th className="excel-th-light legacy-row-label">Tensão [V]</th>
            <td className="excel-td" colSpan={3}>
              <input
                className="excel-input"
                value={dadosCabecalho.tensao}
                onChange={(e) => onChangeCampo("tensao", e.target.value)}
              />
            </td>
            <th className="excel-th-light legacy-row-label">Fator de Potência</th>
            <td className="excel-td">
              <input
                className="excel-input"
                value={dadosCabecalho.fatorPotencia}
                onChange={(e) => onChangeCampo("fatorPotencia", e.target.value)}
              />
            </td>
            <th className="excel-th-light legacy-row-label">Condutores</th>
            <td className="excel-td" colSpan={2}>
              <input
                className="excel-input"
                value={dadosCabecalho.condutores}
                onChange={(e) => onChangeCampo("condutores", e.target.value)}
              />
            </td>
          </tr>
          <tr>
            <th className="excel-th-light legacy-row-label">Localidade</th>
            <td className="excel-td" colSpan={3}>
              <input
                className="excel-input"
                value={dadosCabecalho.localidade}
                onChange={(e) => onChangeCampo("localidade", e.target.value)}
              />
            </td>
            <th className="excel-th-light legacy-row-label">Data</th>
            <td className="excel-td" colSpan={3}>
              <input className="excel-input" value={dadosCabecalho.data} onChange={(e) => onChangeCampo("data", e.target.value)} />
            </td>
            <th className="excel-th-light legacy-row-label">Trafo [kVA]</th>
            <td className="excel-td" colSpan={3}>
              <input
                className="excel-input"
                value={dadosCabecalho.trafoKva}
                onChange={(e) => onChangeCampo("trafoKva", e.target.value)}
              />
            </td>
            <th className="excel-th-light legacy-row-label">Demanda [A]</th>
            <td className="excel-td">
              <input
                className="excel-input"
                value={dadosCabecalho.demanda}
                onChange={(e) => onChangeCampo("demanda", e.target.value)}
              />
            </td>
            <th className="excel-th-light legacy-row-label">Observações</th>
            <td className="excel-td" colSpan={2}>
              <input
                className="excel-input"
                value={dadosCabecalho.observacoes}
                onChange={(e) => onChangeCampo("observacoes", e.target.value)}
              />
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  );
}
