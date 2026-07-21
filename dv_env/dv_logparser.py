#!/usr/bin/env python3
"""Classify a simulation log without modifying the input file."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path


_FAIL_PATTERN = re.compile(r"ERROR|FATAL|Offending|FAIL|TIMEOUT", re.IGNORECASE)
_SEED_PATTERN = re.compile(r"ntb_random_seed=(\d+)")
_PASS_PATTERN = re.compile(r"simulation passed|Simulation_Test_PASSED")
_SUMMARY_PATTERN = re.compile(r"UVM Report(?: catcher)? Summary")


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def parse_log(log_path: Path) -> dict[str, object]:
    path = Path(log_path).expanduser().resolve()
    if not path.is_file():
        return {"status": "FAIL", "reason": f"log does not exist: {path}", "path": str(path)}
    seed = None
    passed = False
    for line_number, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines(), start=1):
        seed_match = _SEED_PATTERN.search(line)
        if seed_match:
            seed = seed_match.group(1)
        if _FAIL_PATTERN.search(line):
            return {
                "status": "FAIL",
                "reason": line,
                "line": line_number,
                "seed": seed,
                "path": str(path),
                "sha256": _sha256(path),
            }
        if _PASS_PATTERN.search(line):
            passed = True
        if _SUMMARY_PATTERN.search(line):
            break
    status = "PASS" if passed else "FAIL"
    return {
        "status": status,
        "reason": "simulation pass marker found" if passed else "no simulation pass marker found",
        "seed": seed,
        "path": str(path),
        "sha256": _sha256(path),
    }


def log_parser(simv_log, is_reg=0, common_msg_filter='', module_msg_filter='', tc_msg_filter=''):
    """Compatibility wrapper returning 0 for PASS and 1 for FAIL."""
    del is_reg, common_msg_filter, module_msg_filter, tc_msg_filter
    result = parse_log(Path(simv_log))
    return 0 if result["status"] == "PASS" else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-s", "--simv-log", required=True, type=Path, help="simulation log to classify")
    parser.add_argument("--report", type=Path, help="optional JSON output path")
    args = parser.parse_args(argv)
    result = parse_log(args.simv_log)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
