from __future__ import annotations

import argparse
from pathlib import Path

from scripts.audit_legacy_cqt import run_audit as run_cqt_audit
from scripts.audit_legacy_tracao import run_audit as run_tracao_audit

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_TARGET_DIR = Path(r"C:\Users\jonat\OneDrive - IM3 Brasil\LIGHT\PROJETOS")
DEFAULT_TRACAO_REPORT = PROJECT_ROOT / "global_audit_report_tracao.csv"
DEFAULT_CQT_REPORT = PROJECT_ROOT / "global_audit_report_cqt.csv"


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Orquestrador global para auditoria resiliente de planilhas legadas LIGHT."
    )
    parser.add_argument(
        "target_dir",
        nargs="?",
        default=str(DEFAULT_TARGET_DIR),
        help="Diretorio raiz com projetos historicos da LIGHT.",
    )
    parser.add_argument(
        "--tracao-report",
        default=str(DEFAULT_TRACAO_REPORT),
        help="Caminho do relatorio CSV global de tracao.",
    )
    parser.add_argument(
        "--cqt-report",
        default=str(DEFAULT_CQT_REPORT),
        help="Caminho do relatorio CSV global de CQT.",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    target_dir = Path(args.target_dir)
    tracao_report = Path(args.tracao_report)
    cqt_report = Path(args.cqt_report)

    print("Iniciando auditoria global de projetos legacy")
    print(f"- Diretorio raiz: {target_dir}")

    tracao_rows = run_tracao_audit(target_dir=target_dir, report_path=tracao_report)
    cqt_rows = run_cqt_audit(target_dir=target_dir, report_path=cqt_report)

    print("Auditoria global finalizada")
    print(f"- Relatorio tracao: {tracao_report} ({len(tracao_rows)} linhas)")
    print(f"- Relatorio CQT: {cqt_report} ({len(cqt_rows)} linhas)")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
