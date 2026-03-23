import React from "react";

const LBL_W = 108;

function classeStatus(estado) {
  if (estado === "APROVADO") return "result-ok";
  if (estado === "ALERTA") return "result-warn";
  if (estado === "REPROVADO") return "result-bad";
  return "";
}

export function LegacySecaoNivel({
  titulo,
  labelResultado,
  travessias,
  onChangeTravessia,
  campos,
  nota,
  statusPorTravessia,
}) {
  const buildAccessibleName = (fieldLabel, travessiaIndex) => `${fieldLabel}, travessia ${travessiaIndex + 1}, ${titulo}`;

  return (
    <div className="sec-panel">
      <div className="sec-title">{titulo}</div>

      <table className="sec-table" style={{ tableLayout: "fixed" }}>
        <colgroup>
          <col style={{ width: LBL_W }} />
          <col style={{ width: "22%" }} />
          <col style={{ width: 18 }} />
          <col style={{ width: "22%" }} />
          <col style={{ width: 18 }} />
          <col style={{ width: "22%" }} />
          <col style={{ width: 18 }} />
          <col style={{ width: "22%" }} />
          <col style={{ width: 18 }} />
        </colgroup>

        <thead>
          <tr>
            <th />
            {travessias.map((_, i) => (
              <th key={i} className="col-hdr" colSpan={2}>{`T${i + 1}`}</th>
            ))}
          </tr>
        </thead>

        <tbody>
          {campos.map(({ campo, label, unidade, isDropdown, opcoes }) => (
            <tr key={campo}>
              <td className="field-lbl">{label}</td>
              {travessias.map((t, i) => {
                const isAlturaField = campo === "alturaPoste" || campo === "alturaAncoragem";
                const shouldHide = isAlturaField && i > 0;

                if (shouldHide) {
                  return (
                    <React.Fragment key={i}>
                      <td />
                      <td className="xunit" />
                    </React.Fragment>
                  );
                }

                return (
                  <React.Fragment key={i}>
                    <td>
                      {isDropdown ? (
                        <select
                          id={`${campo}-t${i + 1}`}
                          className="xcell"
                          style={{ width: "100%" }}
                          value={t[campo] ?? ""}
                          onChange={(e) => onChangeTravessia(i, campo, e.target.value)}
                          aria-label={buildAccessibleName(label, i)}
                        >
                          <option value="">...</option>
                          {(opcoes || []).map((opt) => (
                            <option key={opt} value={opt}>
                              {opt}
                            </option>
                          ))}
                        </select>
                      ) : (
                        <input
                          id={`${campo}-t${i + 1}`}
                          className="xcell"
                          style={{ width: "100%" }}
                          value={t[campo] ?? ""}
                          onChange={(e) => onChangeTravessia(i, campo, e.target.value)}
                          aria-label={buildAccessibleName(label, i)}
                          inputMode="decimal"
                        />
                      )}
                    </td>
                    <td className="xunit">{unidade}</td>
                  </React.Fragment>
                );
              })}
            </tr>
          ))}

          <tr>
            <td className="field-lbl" style={{ fontWeight: 700 }}>Status mecanico</td>
            {travessias.map((_, i) => {
              const status = statusPorTravessia?.[i] || "-";
              return (
                <React.Fragment key={`st-${i}`}>
                  <td className={classeStatus(status)} style={{ textAlign: "center", fontWeight: 700 }}>{status}</td>
                  <td className="xunit" />
                </React.Fragment>
              );
            })}
          </tr>
        </tbody>
      </table>

      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between" }}>
        <span className="res-lbl">{labelResultado}</span>
        {nota ? (
          <span style={{ fontSize: 9, color: "#444", marginRight: 8, textAlign: "right", lineHeight: 1.4 }}>{nota}</span>
        ) : null}
      </div>
    </div>
  );
}
