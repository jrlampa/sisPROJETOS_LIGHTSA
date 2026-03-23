"""Automacao de empacotamento desktop (frontend + PyInstaller)."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
WEB_DIST_DIR = ROOT_DIR / "apps" / "web" / "dist"
NPM_CMD = "npm.cmd" if os.name == "nt" else "npm"


def _run(command: list[str]) -> None:
    print(f"[build_desktop] Executando: {' '.join(command)}")
    subprocess.run(command, check=True, cwd=str(ROOT_DIR))


def build_frontend() -> None:
    """Compila o frontend e valida a existencia de apps/web/dist."""

    _run([NPM_CMD, "--prefix", "apps/web", "run", "build"])

    if not WEB_DIST_DIR.exists() or not WEB_DIST_DIR.is_dir():
        raise RuntimeError("Build do frontend nao gerou apps/web/dist.")

    print(f"[build_desktop] Frontend gerado com sucesso em: {WEB_DIST_DIR}")


def build_executable() -> None:
    """Gera executavel desktop com PyInstaller incluindo os assets do frontend."""

    add_data = f"apps/web/dist{os.pathsep}apps/web/dist"
    _run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--name",
            "sisPROJETOS",
            "--windowed",
            "--add-data",
            add_data,
            "--noconfirm",
            "desktop.py",
        ]
    )

    exe_path = ROOT_DIR / "dist" / "sisPROJETOS.exe"
    folder_path = ROOT_DIR / "dist" / "sisPROJETOS"
    if not exe_path.exists() and not folder_path.exists():
        raise RuntimeError("PyInstaller terminou sem gerar dist/sisPROJETOS.exe ou dist/sisPROJETOS/.")

    if exe_path.exists():
        print(f"[build_desktop] Executavel gerado: {exe_path}")
    else:
        print(f"[build_desktop] Pacote gerado: {folder_path}")


def main() -> None:
    build_frontend()
    build_executable()
    print("[build_desktop] Processo concluido com sucesso.")


if __name__ == "__main__":
    main()