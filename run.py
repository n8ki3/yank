#!/usr/bin/env python3
"""
YANK (YouTube And Kut) - 크로스플랫폼 실행 런처
Windows / macOS / Linux 어디서든 동일하게 동작합니다.

실행 방법:
    python run.py          (Windows)
    python3 run.py         (macOS / Linux)
"""
import os
import sys
import shutil
import platform
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))


def info(msg):
    print(f"  {msg}")


def check_ffmpeg():
    """ffmpeg 사용 가능 여부 확인. Windows는 동봉 exe, 그 외는 시스템 PATH."""
    system = platform.system()
    if system == "Windows":
        local = os.path.join(HERE, "ffmpeg.exe")
        if os.path.exists(local) or shutil.which("ffmpeg"):
            return True
        info("⚠️  ffmpeg.exe를 찾을 수 없습니다. 폴더에 ffmpeg.exe가 있는지 확인하세요.")
        return False
    # macOS / Linux
    if shutil.which("ffmpeg"):
        return True
    if system == "Darwin":
        info("⚠️  ffmpeg가 없습니다.  설치:  brew install ffmpeg")
    else:
        info("⚠️  ffmpeg가 없습니다.  설치:  sudo apt install ffmpeg")
    return False


def install_requirements():
    req = os.path.join(HERE, "requirements.txt")
    if not os.path.exists(req):
        return
    info("📦 의존성 확인/설치 중...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", req],
        cwd=HERE,
    )


def run_app():
    info("🚀 YANK을 실행합니다... (브라우저가 자동으로 열립니다)")
    subprocess.run(
        [sys.executable, "-m", "streamlit", "run", "app.py"],
        cwd=HERE,
    )


def main():
    print("=" * 50)
    print("  🎬 YANK - YouTube And Kut")
    print(f"  OS: {platform.system()}  |  Python: {platform.python_version()}")
    print("=" * 50)

    if not check_ffmpeg():
        info("ffmpeg 설치 후 다시 실행해 주세요.")
        # 그래도 앱은 띄울 수 있게 계속 진행할지 결정 (다운로드 외 기능은 가능)
    install_requirements()
    run_app()


if __name__ == "__main__":
    main()
