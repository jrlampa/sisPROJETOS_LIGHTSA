export function LegacyExcelHeader({ dadosCabecalho, onChangeCampo, tituloAba }) {
  return (
    <table className="excel-table">
      <thead>
        <tr>
          <th className="excel-th-dark" colSpan={8}>
            DADOS DO PROJETO - {tituloAba}
          </th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <th className="excel-th-light">Nome do Projeto</th>
          <td className="excel-td" colSpan={3}>
            <input
              className="excel-input"
              value={dadosCabecalho.nomeProjeto}
              onChange={(e) => onChangeCampo("nomeProjeto", e.target.value)}
            />
          </td>
          <th className="excel-th-light">Projetista</th>
          <td className="excel-td" colSpan={3}>
            <input
              className="excel-input"
              value={dadosCabecalho.projetista}
              onChange={(e) => onChangeCampo("projetista", e.target.value)}
            />
          </td>
        </tr>
        <tr>
          <th className="excel-th-light">Data</th>
          <td className="excel-td">
            <input className="excel-input" value={dadosCabecalho.data} onChange={(e) => onChangeCampo("data", e.target.value)} />
          </td>
          <th className="excel-th-light">Localidade</th>
          <td className="excel-td">
            <input
              className="excel-input"
              value={dadosCabecalho.localidade}
              onChange={(e) => onChangeCampo("localidade", e.target.value)}
            />
          </td>
          <th className="excel-th-light">Condutores</th>
          <td className="excel-td">
            <input
              className="excel-input"
              value={dadosCabecalho.condutores}
              onChange={(e) => onChangeCampo("condutores", e.target.value)}
            />
          </td>
          <th className="excel-th-light">Demanda</th>
          <td className="excel-td">
            <input
              className="excel-input"
              value={dadosCabecalho.demanda}
              onChange={(e) => onChangeCampo("demanda", e.target.value)}
            />
          </td>
        </tr>
        <tr>
          <th className="excel-th-light">Trafo (kVA)</th>
          <td className="excel-td">
            <input
              className="excel-input"
              value={dadosCabecalho.trafoKva}
              onChange={(e) => onChangeCampo("trafoKva", e.target.value)}
            />
          </td>
          <th className="excel-th-light">Tensão (V)</th>
          <td className="excel-td">
            <input
              className="excel-input"
              value={dadosCabecalho.tensao}
              onChange={(e) => onChangeCampo("tensao", e.target.value)}
            />
          </td>
          <th className="excel-th-light">Fator de Potência</th>
          <td className="excel-td">
            <input
              className="excel-input"
              value={dadosCabecalho.fatorPotencia}
              onChange={(e) => onChangeCampo("fatorPotencia", e.target.value)}
            />
          </td>
          <th className="excel-th-light">Observações</th>
          <td className="excel-td">
            <input
              className="excel-input"
              value={dadosCabecalho.observacoes}
              onChange={(e) => onChangeCampo("observacoes", e.target.value)}
            />
          </td>
        </tr>
      </tbody>
    </table>
  );
}
