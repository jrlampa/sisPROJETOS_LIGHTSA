"""Configuracao de logging em ficheiro para API e launcher desktop."""

from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path

LOG_FILENAME = "sisprojetos.log"


def resolve_log_path() -> Path:
    """Resolve o caminho do log para desktop (temp) ou execucao normal (cwd)."""

    desktop_mode = os.getenv("SISPROJETOS_DESKTOP", "0") == "1"
    base_dir = Path(tempfile.gettempdir()) if desktop_mode else Path.cwd()
    return base_dir / LOG_FILENAME


def setup_file_logging(level: int = logging.INFO) -> Path:
    """Configura logging global para ficheiro, evitando handlers duplicados."""

    log_path = resolve_log_path()
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(module)s] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    for handler in root_logger.handlers:
        if isinstance(handler, logging.FileHandler):
            try:
                if Path(handler.baseFilename) == log_path:
                    handler.setFormatter(formatter)
                    return log_path
            except (AttributeError, OSError):
                continue

    file_handler = logging.FileHandler(log_path, encoding="utf-8")
    file_handler.setLevel(level)
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)

    return log_path