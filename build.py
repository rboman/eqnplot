import argparse
import os
import shutil
import subprocess
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parent


def venv_python() -> Path:
    if os.name == "nt":
        return PROJECT_ROOT / ".venv" / "Scripts" / "python.exe"
    return PROJECT_ROOT / ".venv" / "bin" / "python"


def run(command: list[str]) -> None:
    subprocess.run(command, cwd=PROJECT_ROOT, check=True)


def main() -> None:
    parser = argparse.ArgumentParser(description="Cross-platform PyInstaller build helper for EqnPlot.")
    parser.add_argument("--onefile", action="store_true", help="Build a single-file executable.")
    parser.add_argument("--upx", action="store_true", help="Enable UPX compression.")
    args = parser.parse_args()

    python_exe = venv_python()
    if not python_exe.exists():
        raise SystemExit(f"Virtualenv Python not found: {python_exe}")

    icon_path = PROJECT_ROOT / "assets" / "eqnplot-icon.ico"
    data_separator = ";" if os.name == "nt" else ":"

    print("Installing build tools...")
    run([str(python_exe), "-m", "pip", "install", "--upgrade", "pip", "pyinstaller"])

    print("Cleaning build/ and dist/ ...")
    for directory in ("build", "dist"):
        shutil.rmtree(PROJECT_ROOT / directory, ignore_errors=True)

    if args.onefile:
        print("Running PyInstaller in onefile mode...")
        command = [
            str(python_exe),
            "-m",
            "PyInstaller",
            "--noconfirm",
            "--clean",
            "--windowed",
            "--name",
            "EqnPlot",
            "--onefile",
            "--specpath",
            "build",
        ]
        if not args.upx:
            command.append("--noupx")
        if icon_path.exists():
            command += ["--icon", str(icon_path), "--add-data", f"{icon_path}{data_separator}assets"]
        command.append("main.py")
        run(command)
    else:
        print("Running PyInstaller with EqnPlot.spec...")
        env = os.environ.copy()
        env["EQNPLOT_USE_UPX"] = "1" if args.upx else "0"
        subprocess.run(
            [str(python_exe), "-m", "PyInstaller", "--noconfirm", "--clean", "EqnPlot.spec"],
            cwd=PROJECT_ROOT,
            check=True,
            env=env,
        )

    print("Build complete. Output is in dist/")


if __name__ == "__main__":
    main()
