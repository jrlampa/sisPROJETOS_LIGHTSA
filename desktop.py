"""Launcher desktop standalone do sisPROJETOS usando pywebview."""

from __future__ import annotations

import logging
import os
import socket
import threading
import time

import uvicorn
import webview
from PIL import Image, ImageDraw
from pystray import Icon, Menu, MenuItem

from apps.api.core.logger import setup_file_logging


logger = logging.getLogger(__name__)
WINDOW_TITLE = "sisPROJETOS LIGHT S.A."
WINDOW_URL = "http://localhost:8000"


class DesktopRuntime:
    """Orquestra API local, janela pywebview e bandeja do sistema."""

    def __init__(self) -> None:
        self.server: uvicorn.Server | None = None
        self.api_thread: threading.Thread | None = None
        self.tray_icon: Icon | None = None
        self.window: webview.Window | None = None
        self._closing = threading.Event()

    def _run_api(self) -> None:
        """Inicia Uvicorn com controlo de shutdown gracioso."""

        logger.info("Iniciando servidor Uvicorn...")
        config = uvicorn.Config("apps.api.main:app", host="127.0.0.1", port=8000, log_level="info")
        self.server = uvicorn.Server(config)
        self.server.run()

    def _wait_for_api(self, host: str, port: int, timeout: float = 25.0) -> None:
        """Espera a API aceitar conexoes antes de abrir a janela do app."""

        deadline = time.time() + timeout
        while time.time() < deadline:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                if sock.connect_ex((host, port)) == 0:
                    return
            time.sleep(0.2)
        raise RuntimeError("API local nao iniciou dentro do tempo esperado.")

    def _create_tray_image(self) -> Image.Image:
        """Desenha um icone simples para a bandeja do sistema."""

        image = Image.new("RGBA", (64, 64), (15, 23, 42, 255))
        draw = ImageDraw.Draw(image)
        draw.rectangle((8, 8, 56, 56), outline=(245, 158, 11, 255), width=4)
        draw.text((19, 20), "SP", fill=(226, 232, 240, 255))
        return image

    def _show_or_restore_window(self) -> None:
        """Traz a janela para frente ou cria nova janela se necessario."""

        if self.window is None:
            logger.info("Criando nova janela nativa via System Tray.")
            self.window = webview.create_window(WINDOW_TITLE, WINDOW_URL)

        for method_name in ("show", "restore", "bring_to_front"):
            method = getattr(self.window, method_name, None)
            if callable(method):
                try:
                    method()
                except Exception:  # noqa: BLE001
                    logger.debug("Falha ao executar metodo de foco da janela: %s", method_name, exc_info=True)

    def _on_open_menu(self, icon: Icon, item: MenuItem) -> None:
        del icon, item
        self._show_or_restore_window()

    def _on_exit_menu(self, icon: Icon, item: MenuItem) -> None:
        del item
        logger.info("Sair do Sistema acionado pela bandeja.")
        self.shutdown()
        icon.stop()

    def _start_system_tray(self) -> None:
        """Inicia icone e menu da bandeja em thread dedicada."""

        self.tray_icon = Icon(
            "sisPROJETOS",
            self._create_tray_image(),
            WINDOW_TITLE,
            menu=Menu(
                MenuItem("Abrir sisPROJETOS", self._on_open_menu),
                MenuItem("Sair do Sistema", self._on_exit_menu),
            ),
        )
        self.tray_icon.run()

    def _on_window_closing(self, *args) -> bool:
        """Interceta o fechar da janela para manter app residente na bandeja."""

        del args

        if self._closing.is_set():
            return True

        logger.info("Janela fechada pelo utilizador; aplicacao permanece na bandeja.")
        if self.window is not None:
            hide_method = getattr(self.window, "hide", None)
            if callable(hide_method):
                try:
                    hide_method()
                except Exception:  # noqa: BLE001
                    logger.debug("Falha ao ocultar janela apos evento de closing.", exc_info=True)
        return False

    def shutdown(self) -> None:
        """Executa encerramento gracioso de janela e servidor API."""

        if self._closing.is_set():
            return
        self._closing.set()

        if self.window is not None:
            try:
                self.window.destroy()
            except Exception:  # noqa: BLE001
                logger.debug("Falha ao destruir janela durante shutdown.", exc_info=True)

        if self.server is not None:
            self.server.should_exit = True

        if self.api_thread is not None and self.api_thread.is_alive():
            self.api_thread.join(timeout=8)

        stop_method = getattr(webview, "stop", None)
        if callable(stop_method):
            try:
                stop_method()
            except Exception:  # noqa: BLE001
                logger.debug("Falha ao parar loop do pywebview.", exc_info=True)

    def run(self) -> None:
        """Inicializa runtime desktop completo."""

        os.environ.setdefault("SISPROJETOS_DESKTOP", "1")
        log_path = setup_file_logging()
        logger.info("Logging desktop configurado em: %s", log_path)

        self.api_thread = threading.Thread(target=self._run_api, name="sisprojetos-api", daemon=True)
        self.api_thread.start()
        self._wait_for_api("127.0.0.1", 8000)

        self.window = webview.create_window(WINDOW_TITLE, WINDOW_URL)
        self.window.events.closing += self._on_window_closing

        tray_thread = threading.Thread(target=self._start_system_tray, name="sisprojetos-tray", daemon=True)
        tray_thread.start()

        logger.info("Abrindo janela nativa...")
        try:
            webview.start()
        finally:
            self.shutdown()


def main() -> None:
    runtime = DesktopRuntime()
    runtime.run()


if __name__ == "__main__":
    main()
