"""Focused isolated checks for retained secondary address-planner entry points."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
HARNESS_ROOT = PROJECT_ROOT.parents[2] / "prompts" / "tool_skill_parallel_dev"


def _environment() -> dict[str, str]:
    environment = os.environ.copy()
    environment["ADDRESS_PLANNER_ROOT"] = str(PROJECT_ROOT)
    environment["UHDL_ROOT"] = str(PROJECT_ROOT.parent / "uhdl")
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment.pop("PYTHONPATH", None)
    environment.pop("PYTHONHOME", None)
    return environment


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_excel_cli_generates_only_below_requested_output(tmp_path: Path) -> None:
    fixture = PROJECT_ROOT / "excel" / "excel_demo" / "regbank_demo.xlsx"
    completed = subprocess.run(
        [sys.executable, str(PROJECT_ROOT / "regbuilder.py"), "-e", str(fixture), "-o", str(tmp_path)],
        text=True,
        capture_output=True,
        env=_environment(),
        check=False,
    )
    assert completed.returncode == 0, completed.stderr
    payload = json.loads(completed.stdout.splitlines()[-1])
    assert Path(payload["script"]).is_file()
    assert (tmp_path / "datalog.txt").is_file()
    assert (tmp_path / "generated" / "reg_bank_table" / "html" / "data.json").is_file()


def test_ralf_module_cli_uses_package_resource_and_reports_missing_input(tmp_path: Path) -> None:
    fixture = PROJECT_ROOT / "address_planner" / "ralf_parser" / "test.ralf"
    command = [
        sys.executable,
        "-m",
        "address_planner.ralf_parser.main",
        "--input",
        str(fixture),
        "--output-dir",
        str(tmp_path / "valid"),
        "--report",
        str(tmp_path / "valid" / "report.json"),
    ]
    completed = subprocess.run(command, text=True, capture_output=True, env=_environment(), check=False)
    assert completed.returncode == 0, completed.stderr
    report = json.loads((tmp_path / "valid" / "report.json").read_text(encoding="utf-8"))
    assert report["input_sha256"] == _sha256(fixture)
    assert (tmp_path / "valid" / "ralf_import" / "html" / "data.json").is_file()

    missing_command = list(command)
    missing_command[4] = str(tmp_path / "missing.ralf")
    missing = subprocess.run(
        missing_command,
        text=True,
        capture_output=True,
        env=_environment(),
        check=False,
    )
    assert missing.returncode == 2
    assert "does not exist" in missing.stderr


def test_matrix_fixed_model_report_and_rejects_unknown_connection(tmp_path: Path) -> None:
    from address_planner import MatrixSpace

    fixture = HARNESS_ROOT / "runs" / "session_02" / "matrix_model.json"
    report_path = MatrixSpace.report_fixed_model(fixture, tmp_path)
    report = json.loads(report_path.read_text(encoding="utf-8"))
    assert report["model"]["model_id"] == "matrix_report_model"
    assert report["model"]["connections"] == {"cpu": ["sram", "peripheral"], "dma": ["sram"]}

    invalid = dict(report["model"])
    invalid["connections"] = dict(invalid["connections"])
    invalid["connections"]["cpu"] = ["missing"]
    with pytest.raises(ValueError, match="names no slave"):
        MatrixSpace.from_fixed_model(invalid)


def test_dv_log_parser_is_non_mutating_and_has_process_status(tmp_path: Path) -> None:
    fixture = HARNESS_ROOT / "runs" / "session_02" / "dv_pass.log"
    passing_log = tmp_path / "pass.log"
    passing_log.write_bytes(fixture.read_bytes())
    before = _sha256(passing_log)
    command = [
        sys.executable,
        str(PROJECT_ROOT / "dv_env" / "dv_logparser.py"),
        "--simv-log",
        str(passing_log),
        "--report",
        str(tmp_path / "pass.json"),
    ]
    passing = subprocess.run(command, text=True, capture_output=True, env=_environment(), check=False)
    assert passing.returncode == 0, passing.stderr
    assert _sha256(passing_log) == before
    assert json.loads((tmp_path / "pass.json").read_text(encoding="utf-8"))["status"] == "PASS"

    failing_log = tmp_path / "fail.log"
    failing_log.write_text("ntb_random_seed=7\nFATAL injected failure\n", encoding="utf-8")
    failing = subprocess.run(
        [*command[:3], str(failing_log), "--report", str(tmp_path / "fail.json")],
        text=True,
        capture_output=True,
        env=_environment(),
        check=False,
    )
    assert failing.returncode != 0
    assert json.loads((tmp_path / "fail.json").read_text(encoding="utf-8"))["status"] == "FAIL"
