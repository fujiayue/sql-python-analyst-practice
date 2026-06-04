from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import time
import urllib.request
import webbrowser


APP_URL = "http://127.0.0.1:5173"
API_HEALTH = "http://127.0.0.1:8000/api/health"
CREATE_NO_WINDOW = 0x08000000 if os.name == "nt" else 0


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def wait_for_url(url: str, seconds: int = 30) -> bool:
    deadline = time.time() + seconds
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status < 500:
                    return True
        except Exception:
            time.sleep(1)
    return False


def run_setup(root: Path) -> None:
    setup_script = root / "scripts" / "setup.ps1"
    print("首次运行需要安装本地依赖，可能需要几分钟。")
    subprocess.check_call(
        [
            "powershell",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(setup_script),
        ],
        cwd=root,
    )


def ensure_environment(root: Path) -> None:
    python_exe = root / ".venv" / "Scripts" / "python.exe"
    npm_modules = root / "frontend" / "node_modules"
    if not python_exe.exists() or not npm_modules.exists():
        run_setup(root)


def start_backend(root: Path) -> None:
    if wait_for_url(API_HEALTH, seconds=2):
        print("后端已在运行。")
        return
    log_dir = root / "backend" / ".local"
    log_dir.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["PYTHONPATH"] = str(root)
    subprocess.Popen(
        [
            str(root / ".venv" / "Scripts" / "python.exe"),
            "-m",
            "uvicorn",
            "backend.app.main:app",
            "--host",
            "127.0.0.1",
            "--port",
            "8000",
        ],
        cwd=root,
        env=env,
        stdout=(log_dir / "backend.out.log").open("a", encoding="utf-8"),
        stderr=(log_dir / "backend.err.log").open("a", encoding="utf-8"),
        creationflags=CREATE_NO_WINDOW,
    )
    print("正在启动后端。")


def start_frontend(root: Path) -> None:
    if wait_for_url(APP_URL, seconds=2):
        print("前端已在运行。")
        return
    log_dir = root / "backend" / ".local"
    log_dir.mkdir(parents=True, exist_ok=True)
    subprocess.Popen(
        ["cmd", "/c", "npm run dev -- --host 127.0.0.1"],
        cwd=root / "frontend",
        stdout=(log_dir / "frontend.out.log").open("a", encoding="utf-8"),
        stderr=(log_dir / "frontend.err.log").open("a", encoding="utf-8"),
        creationflags=CREATE_NO_WINDOW,
    )
    print("正在启动前端。")


def main() -> int:
    root = app_root()
    print("本地机考训练器启动器")
    print(f"项目目录：{root}")
    try:
        ensure_environment(root)
        start_backend(root)
        if not wait_for_url(API_HEALTH, seconds=45):
            raise RuntimeError("后端启动超时，请查看 backend/.local/backend.err.log")
        start_frontend(root)
        if not wait_for_url(APP_URL, seconds=45):
            raise RuntimeError("前端启动超时，请查看 backend/.local/frontend.err.log")
        webbrowser.open(APP_URL)
        print(f"已打开：{APP_URL}")
        print("可以关闭这个启动器窗口；训练器会继续在后台运行。")
        time.sleep(5)
        return 0
    except Exception as exc:
        print(f"启动失败：{exc}")
        print("按回车退出。")
        try:
            input()
        except EOFError:
            pass
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

