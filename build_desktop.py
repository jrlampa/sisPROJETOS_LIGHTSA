"""Automacao de empacotamento desktop (frontend + PyInstaller)."""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
WEB_DIST_DIR = ROOT_DIR / "apps" / "web" / "dist"
OUTPUT_DIR = ROOT_DIR / "Output"
PYI_DIST_DIR = ROOT_DIR / "dist_desktop"
PYI_WORK_DIR = ROOT_DIR / "build_pyinstaller"
NPM_CMD = "npm.cmd" if os.name == "nt" else "npm"
ISCC_CANDIDATES = [
    Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
    Path(r"C:\Program Files\Inno Setup 6\ISCC.exe"),
]

LOGGER = logging.getLogger("build_desktop")


def _run(command: list[str]) -> None:
    LOGGER.info("Executando: %s", " ".join(command))
    subprocess.run(command, check=True, cwd=str(ROOT_DIR))


def _safe_rmtree(path: Path, retries: int = 5, delay_seconds: float = 0.7) -> None:
    """Remove diretorio com tentativas extras para contornar locks temporarios no Windows."""

    if not path.exists():
        return

    for attempt in range(1, retries + 1):
        try:
            shutil.rmtree(path)
            return
        except PermissionError:
            if attempt == retries:
                raise
            time.sleep(delay_seconds)


def build_frontend() -> None:
    """Compila o frontend e valida a existencia de apps/web/dist."""

    _run([NPM_CMD, "--prefix", "apps/web", "run", "build"])

    if not WEB_DIST_DIR.exists() or not WEB_DIST_DIR.is_dir():
        raise RuntimeError("Build do frontend nao gerou apps/web/dist.")

    LOGGER.info("Frontend gerado com sucesso em: %s", WEB_DIST_DIR)


def build_executable() -> None:
    """Gera executavel desktop com PyInstaller incluindo os assets do frontend."""

    _safe_rmtree(PYI_DIST_DIR / "sisPROJETOS")
    _safe_rmtree(PYI_WORK_DIR)

    add_data = f"apps/web/dist{os.pathsep}apps/web/dist"
    _run(
        [
            sys.executable,
            "-m",
            "PyInstaller",
            "--name",
            "sisPROJETOS",
            "--windowed",
            "--exclude-module",
            "tkinter",
            "--exclude-module",
            "unittest",
            "--exclude-module",
            "pydoc",
            "--exclude-module",
            "pdb",
            "--exclude-module",
            "email",
            "--add-data",
            add_data,
            "--distpath",
            str(PYI_DIST_DIR),
            "--workpath",
            str(PYI_WORK_DIR),
            "--noconfirm",
            "desktop.py",
        ]
    )

    exe_path = PYI_DIST_DIR / "sisPROJETOS.exe"
    folder_path = PYI_DIST_DIR / "sisPROJETOS"
    if not exe_path.exists() and not folder_path.exists():
        raise RuntimeError("PyInstaller terminou sem gerar dist_desktop/sisPROJETOS.exe ou dist_desktop/sisPROJETOS/.")

    if exe_path.exists():
        LOGGER.info("Executavel gerado: %s", exe_path)
    else:
        LOGGER.info("Pacote gerado: %s", folder_path)


def _find_iscc() -> Path | None:
    """Localiza o compilador de script do Inno Setup nos caminhos padrao."""

    for candidate in ISCC_CANDIDATES:
        if candidate.exists():
            return candidate
    return None


def build_installer() -> None:
    """Compila o instalador final com Inno Setup em modo headless."""

    iscc_path = _find_iscc()
    if iscc_path is None:
        LOGGER.warning(
            "Inno Setup nao encontrado. O executavel standalone foi gerado, mas o instalador final foi ignorado."
        )
        return

    iss_file = ROOT_DIR / "build_installer.iss"
    if not iss_file.exists():
        raise RuntimeError("Arquivo build_installer.iss nao encontrado na raiz do projeto.")

    build_source_dir = str((PYI_DIST_DIR / "sisPROJETOS").relative_to(ROOT_DIR))
    _run([str(iscc_path), f"/DBuildSourceDir={build_source_dir}", str(iss_file)])

    installer_path = OUTPUT_DIR / "Instalar_sisPROJETOS.exe"
    if installer_path.exists():
        LOGGER.info("Instalador gerado: %s", installer_path)
    else:
        raise RuntimeError("Inno Setup executado, mas o instalador nao foi encontrado em Output.")


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="[build_desktop] %(message)s")
    build_frontend()
    build_executable()
    build_installer()
    LOGGER.info("Processo concluido.")


if __name__ == "__main__":
    main()