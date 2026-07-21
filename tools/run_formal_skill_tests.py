#!/usr/bin/env python3
"""Run real formal-skill tests without writing caches into the skill package."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

if __package__:
    from .formal_skill_guard import GuardError, snapshot, verify
else:
    from formal_skill_guard import GuardError, snapshot, verify


SCHEMA_VERSION = 1


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as stream:
            temporary = Path(stream.name)
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def _outside_skill(skill_root: Path, path: Path, label: str) -> Path:
    resolved = path.expanduser().resolve()
    if resolved == skill_root or skill_root in resolved.parents:
        raise GuardError(f"{label} must be outside the formal skill package: {resolved}")
    return resolved


def _run(command: list[str], environment: dict[str, str], log: Path) -> int:
    try:
        completed = subprocess.run(
            command,
            env=environment,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            check=False,
        )
        output = completed.stdout
        exit_code = completed.returncode
    except OSError as error:
        output = f"cannot execute command: {error}\n"
        exit_code = 127
    log.write_text(output, encoding="utf-8")
    return exit_code


def _junit_counts(path: Path) -> dict[str, int] | None:
    if not path.is_file():
        return None
    root = ET.parse(path).getroot()
    suites = list(root.iter("testsuite"))
    return {
        key: sum(int(suite.get(key, 0)) for suite in suites)
        for key in ("tests", "failures", "errors", "skipped")
    }


def run(arguments: argparse.Namespace) -> dict[str, Any]:
    skill_root = arguments.skill_root.expanduser().resolve()
    if not skill_root.is_dir() or skill_root.is_symlink():
        raise GuardError(f"formal skill root must be a real directory: {skill_root}")
    runtime_root = arguments.address_planner_root.expanduser().resolve()
    uhdl_root = arguments.uhdl_root.expanduser().resolve()
    if not (runtime_root / "address_planner" / "__init__.py").is_file():
        raise GuardError(f"invalid Address Planner root: {runtime_root}")
    if not (uhdl_root / "uhdl" / "__init__.py").is_file():
        raise GuardError(f"invalid canonical U-HDL root: {uhdl_root}")

    work_root = _outside_skill(skill_root, arguments.work_root, "work root")
    manifest = _outside_skill(skill_root, arguments.manifest, "manifest")
    junit = _outside_skill(skill_root, arguments.junit, "JUnit report")
    work_root.mkdir(parents=True, exist_ok=True)
    manifest.parent.mkdir(parents=True, exist_ok=True)
    junit.parent.mkdir(parents=True, exist_ok=True)
    test_paths = [(skill_root / relative).resolve() for relative in arguments.test]
    for test_path in test_paths:
        if not test_path.is_file() or skill_root not in test_path.parents:
            raise GuardError(f"formal skill test escaped or is missing: {test_path}")
    quick_validate = arguments.quick_validate.expanduser().resolve()
    if not quick_validate.is_file():
        raise GuardError(f"quick validation script is missing: {quick_validate}")
    quick_validate_python = arguments.quick_validate_python.expanduser().resolve()
    if not quick_validate_python.is_file():
        raise GuardError(f"quick validation Python is missing: {quick_validate_python}")

    pre_report = work_root / "formal_skill_pre.json"
    post_report = work_root / "formal_skill_post.json"
    pytest_log = work_root / "skill_pytest.log"
    quick_log = work_root / "quick_validate.log"
    pytest_tmp = work_root / "pytest_tmp"
    environment = os.environ.copy()
    for name in ("PYTHONHOME", "PYTHONPATH", "PYTHONPYCACHEPREFIX", "PYTEST_ADDOPTS"):
        environment.pop(name, None)
    environment.update(
        {
            "ADDRESS_PLANNER_ROOT": str(runtime_root),
            "UHDL_ROOT": str(uhdl_root),
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        }
    )
    pytest_command = [
        str(arguments.python.resolve()),
        "-m",
        "pytest",
        "-q",
        "-rA",
        "-p",
        "no:cacheprovider",
        "--basetemp",
        str(pytest_tmp),
        f"--junitxml={junit}",
        *(str(path) for path in test_paths),
    ]
    quick_command = [str(quick_validate_python), "-B", str(quick_validate), str(skill_root)]

    before = snapshot(skill_root, pre_report)
    pytest_exit = 127
    quick_exit = 127
    post: dict[str, Any]
    try:
        pytest_exit = _run(pytest_command, environment, pytest_log)
        quick_exit = _run(quick_command, environment, quick_log)
    finally:
        post = verify(skill_root, pre_report, post_report)

    counts = _junit_counts(junit)
    junit_clean = counts is not None and all(counts[key] == 0 for key in ("failures", "errors", "skipped"))
    result = (
        "pass"
        if pytest_exit == 0
        and quick_exit == 0
        and junit_clean
        and post["formal_package_unchanged"]
        else "fail"
    )
    payload: dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "result": result,
        "manifest": str(manifest),
        "formal_skill_root": str(skill_root),
        "work_root": str(work_root),
        "environment": {
            "ADDRESS_PLANNER_ROOT": str(runtime_root),
            "UHDL_ROOT": str(uhdl_root),
            "PYTHONHOME": "unset",
            "PYTHONPATH": "unset",
            "PYTHONPYCACHEPREFIX": "unset",
            "PYTEST_ADDOPTS": "unset",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        },
        "pytest": {
            "argv": pytest_command,
            "exit_code": pytest_exit,
            "log": {"path": str(pytest_log), "size_bytes": pytest_log.stat().st_size, "sha256": _sha256(pytest_log)},
            "junit": None if not junit.is_file() else {"path": str(junit), "size_bytes": junit.stat().st_size, "sha256": _sha256(junit), "counts": counts},
        },
        "quick_validate": {
            "argv": quick_command,
            "exit_code": quick_exit,
            "log": {"path": str(quick_log), "size_bytes": quick_log.stat().st_size, "sha256": _sha256(quick_log)},
        },
        "formal_skill_inventory": {
            "pre": {"path": str(pre_report), "size_bytes": pre_report.stat().st_size, "sha256": _sha256(pre_report)},
            "post": {"path": str(post_report), "size_bytes": post_report.stat().st_size, "sha256": _sha256(post_report)},
            "before_package_digest": before["package_digest"],
            "after_package_digest": post["after_package_digest"],
            "before_cache_digest": before["cache_digest"],
            "after_cache_digest": post["after_cache_digest"],
            "preexisting_cache_paths": post["preexisting_cache_paths"],
            "cache_mutations": post["cache_mutations"],
            "formal_package_unchanged": post["formal_package_unchanged"],
        },
    }
    _write_json(manifest, payload)
    return payload


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skill-root", required=True, type=Path)
    parser.add_argument("--address-planner-root", required=True, type=Path)
    parser.add_argument("--uhdl-root", required=True, type=Path)
    parser.add_argument("--work-root", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--junit", required=True, type=Path)
    parser.add_argument("--quick-validate", required=True, type=Path)
    parser.add_argument("--quick-validate-python", required=True, type=Path)
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    parser.add_argument("--test", required=True, action="append")
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        payload = run(_parser().parse_args(argv))
    except (GuardError, ET.ParseError) as error:
        print(json.dumps({"result": "error", "error": str(error)}, sort_keys=True))
        return 2
    print(
        json.dumps(
            {
                "result": payload["result"],
                "manifest": payload["manifest"],
                "pytest_exit_code": payload["pytest"]["exit_code"],
                "quick_validate_exit_code": payload["quick_validate"]["exit_code"],
                "formal_package_unchanged": payload["formal_skill_inventory"]["formal_package_unchanged"],
                "cache_mutations": payload["formal_skill_inventory"]["cache_mutations"],
            },
            sort_keys=True,
        )
    )
    return 0 if payload["result"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
