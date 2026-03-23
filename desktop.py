"""Launcher desktop standalone do sisPROJETOS usando pywebview."""

from __future__ import annotations

import logging
import os
import socket
import threading
import time

import uvicorn
import webview

from apps.api.core.logger import setup_file_logging


logger = logging.getLogger(__name__)


def _run_api() -> None:
    """Inicia a API FastAPI no processo local para consumo da UI desktop."""

    logger.info("Iniciando servidor Uvicorn...")
    uvicorn.run("apps.api.main:app", host="127.0.0.1", port=8000, log_level="info")


def _wait_for_api(host: str, port: int, timeout: float = 25.0) -> None:
    """Espera a API aceitar conexoes antes de abrir a janela do app."""

    deadline = time.time() + timeout
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex((host, port)) == 0:
                return
        time.sleep(0.2)
    raise RuntimeError("API local nao iniciou dentro do tempo esperado.")


def main() -> None:
    os.environ.setdefault("SISPROJETOS_DESKTOP", "1")
    log_path = setup_file_logging()
    logger.info("Logging desktop configurado em: %s", log_path)

    api_thread = threading.Thread(target=_run_api, name="sisprojetos-api", daemon=True)
    api_thread.start()

    _wait_for_api("127.0.0.1", 8000)

    logger.info("Abrindo janela nativa...")
    webview.create_window("sisPROJETOS LIGHT S.A.", "http://localhost:8000")
    webview.start()


if __name__ == "__main__":
    main()
