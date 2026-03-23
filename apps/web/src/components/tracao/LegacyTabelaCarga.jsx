export function LegacyTabelaCarga({ dados }) {
  return (
    <div style={{ marginTop: 8, width: "100%", overflowX: "auto" }}>
      <table className="sec-table" style={{ fontSize: 9 }}>
        <thead>
          <tr>
            <th rowSpan={2}>a °</th>
            <th colSpan={2}>R (daN)</th>
          </tr>
          <tr>
            <th>300</th>
            <th>600</th>
          </tr>
        </thead>
        <tbody>
          {dados.map((row, i) => (
            <tr key={i}>
              <td style={{ textAlign: "center" }}>{row.alpha}</td>
              <td style={{ textAlign: "center" }}>{row.R300}</td>
              <td style={{ textAlign: "center" }}>{row.R600}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
