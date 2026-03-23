import { memo, useId } from "react";

export const LegacyDiagramaPoste = memo(function LegacyDiagramaPoste() {
  const rawId = useId();
  const safeId = rawId.replace(/:/g, "");
  const markerDownId = `${safeId}-arr-d`;
  const markerRightId = `${safeId}-arr-r`;
  const captionId = `${safeId}-caption`;

  return (
    <figure className="diagrama-poste-figure" style={{ marginTop: 10 }}>
      <svg width={170} height={145} viewBox="0 0 170 145" role="img" aria-label="Diagrama do poste" aria-describedby={captionId}>
        <defs>
          <marker id={markerDownId} markerWidth="5" markerHeight="5" refX="2.5" refY="5" orient="auto">
            <path d="M0,0 L5,0 L2.5,5 z" fill="#1f1f1f" />
          </marker>
          <marker id={markerRightId} markerWidth="5" markerHeight="5" refX="5" refY="2.5" orient="auto">
            <path d="M0,0 L0,5 L5,2.5 z" fill="#1f1f1f" />
          </marker>
        </defs>

        <rect x={76} y={18} width={7} height={72} fill="#555" rx={1} />
        <rect x={57} y={88} width={45} height={5} fill="#444" rx={1} />
        <rect x={63} y={93} width={33} height={4} fill="#333" rx={1} />
        <rect x={69} y={97} width={21} height={8} fill="#222" rx={1} />

        <line x1={80} y1={2} x2={80} y2={17} stroke="#1f1f1f" strokeWidth={1.5} markerEnd={`url(#${markerDownId})`} />
        <text x={87} y={10} fontSize={8.5} fill="#1f1f1f" fontStyle="italic" fontFamily="Calibri,Arial">C</text>
        <text x={94} y={12} fontSize={7} fill="#1f1f1f" fontFamily="Calibri,Arial">N</text>

        <line x1={80} y1={48} x2={122} y2={72} stroke="#1f1f1f" strokeWidth={1.4} markerEnd={`url(#${markerRightId})`} />
        <text x={107} y={53} fontSize={9} fill="#1f1f1f" fontStyle="italic" fontFamily="Calibri,Arial">R</text>

        <path d="M 80 60 A 14 14 0 0 1 87 48" stroke="#1f1f1f" strokeWidth={0.9} fill="none" />
        <text x={88} y={60} fontSize={8} fill="#1f1f1f" fontFamily="Calibri,Arial">a</text>

        <line x1={80} y1={70} x2={122} y2={70} stroke="#1f1f1f" strokeWidth={1.4} markerEnd={`url(#${markerRightId})`} />
        <text x={84} y={82} fontSize={7.5} fill="#1f1f1f" fontFamily="Calibri,Arial">1/2 C</text>
        <text x={116} y={84} fontSize={6} fill="#1f1f1f" fontFamily="Calibri,Arial">N</text>
      </svg>

      <figcaption id={captionId} className="diagrama-poste-caption" style={{ fontSize: 7.5, color: "#333", lineHeight: 1.45, maxWidth: 192, marginTop: 2 }}>
        <p>C_N - Carga Nominal do poste, na direcao da face de maior resistencia.</p>
        <p>R - Carga maxima de utilizacao do poste na direcao do angulo a.</p>
        <p>a - Angulo que a carga maxima faz com a face de maior resistencia nominal.</p>
      </figcaption>
    </figure>
  );
});
