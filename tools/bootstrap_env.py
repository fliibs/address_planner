#!/usr/bin/env python3
"""Create the explicit isolated environment used by address-planner commands."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
import venv
from pathlib import Path


def _root(variable: str, required: Path) -> Path:
    value = os.environ.get(variable)
    if not value:
        raise SystemExit(f"{variable} is required")
    root = Path(value).expanduser().resolve()
    if root != required:
        raise SystemExit(f"{variable} must name this checkout: {required}")
    return root


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="bootstrap isolated address-planner Python environment")
    parser.add_argument("--venv", required=True, type=Path, help="target virtualenv path")
    parser.add_argument("--with-test", action="store_true", help="install the pinned test dependencies")
    args = parser.parse_args(argv)

    project_root = Path(__file__).resolve().parents[1]
    planner_root = _root("ADDRESS_PLANNER_ROOT", project_root)
    uhdl_root = Path(os.environ.get("UHDL_ROOT", "")).expanduser().resolve()
    if not (uhdl_root / "uhdl" / "__init__.py").is_file():
        raise SystemExit("UHDL_ROOT must contain uhdl/__init__.py and cannot be empty")
    if uhdl_root == project_root / "address_planner" / "uhdl":
        raise SystemExit("UHDL_ROOT must not point at the nested legacy snapshot")

    venv_dir = args.venv.resolve()
    venv.EnvBuilder(with_pip=True, clear=False).create(venv_dir)
    python = venv_dir / ("Scripts/python.exe" if sys.platform == "win32" else "bin/python")
    requirements = project_root / "requirements" / "runtime.lock"
    command = [str(python), "-m", "pip", "install", "--disable-pip-version-check", "--no-input", "-r", str(requirements)]
    if args.with_test:
        command.extend(["-r", str(project_root / "requirements" / "test.lock")])
    subprocess.run(command, check=True)

    site_packages = subprocess.check_output(
        [str(python), "-c", "import site; print(site.getsitepackages()[0])"], text=True
    ).strip()
    pth = Path(site_packages) / "address_planner_runtime_roots.pth"
    pth.write_text(f"{planner_root}\n{uhdl_root}\n", encoding="utf-8")
    print(f"bootstrapped {venv_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
