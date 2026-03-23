from __future__ import annotations

import os
import shutil
import signal
import subprocess
import sys
import threading
from typing import TextIO

BLUE = "\033[94m"
GREEN = "\033[92m"
RESET = "\033[0m"


def resolve_executable(*candidates: str) -> str:
    """Return the first executable found in PATH from the given candidates."""
    for candidate in candidates:
        resolved = shutil.which(candidate)
        if resolved:
            return resolved
    raise FileNotFoundError(f"Executavel nao encontrado no PATH: {', '.join(candidates)}")


def stream_logs(prefix: str, color: str, stream: TextIO) -> None:
    """Stream process output line-by-line with a colored prefix."""
    try:
        for line in iter(stream.readline, ""):
            if not line:
                break
            print(f"{color}[{prefix}]{RESET} {line.rstrip()}")
    finally:
        stream.close()


def terminate_process(proc: subprocess.Popen[str], name: str) -> None:
    """Terminate a subprocess gracefully, escalating to kill if needed."""
    if proc.poll() is not None:
        return

    print(f"Encerrando {name}...")
    if os.name == "nt":
        if name == "WEB":
            subprocess.run(
                ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                capture_output=True,
                text=True,
                check=False,
            )
            try:
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
            return
        try:
            proc.send_signal(signal.CTRL_BREAK_EVENT)
        except (ValueError, OSError):
            proc.terminate()
    else:
        proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        print(f"{name} nao encerrou a tempo; forçando finalizacao.")
        proc.kill()


def main() -> int:
    npm_exe = resolve_executable("npm.cmd", "npm")
    python_exe = sys.executable

    web_cmd = [npm_exe, "--prefix", "apps/web", "run", "dev"]
    api_cmd = [python_exe, "-m", "uvicorn", "apps.api.main:app", "--reload", "--port", "8000"]
    web_env = os.environ.copy()
    web_env.setdefault("VITE_API_BASE_URL", "http://127.0.0.1:8000/api")

    creationflags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == "nt" else 0

    web_proc = subprocess.Popen(
        web_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        creationflags=creationflags,
        env=web_env,
    )
    api_proc = subprocess.Popen(
        api_cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
        creationflags=creationflags,
    )

    web_thread = threading.Thread(
        target=stream_logs,
        args=("WEB", BLUE, web_proc.stdout),
        daemon=True,
    )
    api_thread = threading.Thread(
        target=stream_logs,
        args=("API", GREEN, api_proc.stdout),
        daemon=True,
    )

    web_thread.start()
    api_thread.start()

    stop_event = threading.Event()

    def handle_shutdown(sig: int, _frame: object) -> None:
        _ = sig
        if stop_event.is_set():
            return
        stop_event.set()
        print("\nCtrl+C recebido. Encerrando processos...")
        terminate_process(web_proc, "WEB")
        terminate_process(api_proc, "API")

    signal.signal(signal.SIGINT, handle_shutdown)

    try:
        while not stop_event.is_set():
            if web_proc.poll() is not None:
                print("Processo WEB finalizou.")
                stop_event.set()
                terminate_process(api_proc, "API")
                break

            if api_proc.poll() is not None:
                print("Processo API finalizou.")
                stop_event.set()
                terminate_process(web_proc, "WEB")
                break

            stop_event.wait(0.5)
    except KeyboardInterrupt:
        handle_shutdown(signal.SIGINT, None)

    web_thread.join(timeout=2)
    api_thread.join(timeout=2)

    web_code = web_proc.poll() if web_proc.poll() is not None else 0
    api_code = api_proc.poll() if api_proc.poll() is not None else 0

    if stop_event.is_set() and (web_code in (0, -15) and api_code in (0, -15)):
        return 0

    if web_code not in (0, -15):
        return int(web_code)
    if api_code not in (0, -15):
        return int(api_code)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
