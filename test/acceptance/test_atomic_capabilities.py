"""Focused transactional publication tests for the A08 capability evidence bundle."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

import address_planner.selftest as selftest
import address_planner.GlobalValues as global_values


ROOT = Path(__file__).resolve().parents[2]
WORKFLOW_ROOT = ROOT.parents[2] / "prompts" / "tool_skill_parallel_dev"
FIXTURES = WORKFLOW_ROOT / "runs" / "session_02"
CONTRACT = WORKFLOW_ROOT / "results" / "session_02_baseline_contract.json"


def _digest_tree(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        rel = path.relative_to(root).as_posix().encode("utf-8")
        if path.is_dir():
            digest.update(b"D\0" + rel + b"\0")
        elif path.is_symlink():
            digest.update(b"L\0" + rel + b"\0" + os.readlink(path).encode("utf-8"))
        else:
            digest.update(b"F\0" + rel + b"\0" + hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def _arguments(work: Path) -> dict[str, Path]:
    acceptance = work / "acceptance"
    return {
        "manifest": acceptance / "delivery_manifest.json",
        "baseline_contract": CONTRACT,
        "capability_report": acceptance / "capabilities.json",
        "secondary_output_dir": acceptance / "secondary",
        "excel_input": ROOT / "excel" / "excel_demo" / "regbank_demo.xlsx",
        "ralf_input": ROOT / "address_planner" / "ralf_parser" / "test.ralf",
        "bus_models": FIXTURES / "bus_interface_models.json",
        "advanced_models": FIXTURES / "advanced_construct_models.json",
        "matrix_model": FIXTURES / "matrix_model.json",
        "dv_log_input": FIXTURES / "dv_pass.log",
    }


def _call(arguments: dict[str, Path]) -> dict:
    return selftest.capabilities(**arguments)


@pytest.fixture()
def published_bundle(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    monkeypatch.setenv("ADDRESS_PLANNER_ROOT", str(ROOT))
    monkeypatch.setenv("UHDL_ROOT", str(ROOT.parent / "uhdl"))
    acceptance = tmp_path / "acceptance"
    acceptance.mkdir()
    model = FIXTURES / "representative_register_model.json"
    manifest = acceptance / "delivery_manifest.json"
    selftest.preflight(acceptance / "preflight.json")
    (acceptance / "unit_tests.xml").write_text(
        '<testsuites><testsuite tests="1" failures="0" errors="0" skipped="0"/></testsuites>\n',
        encoding="utf-8",
    )
    selftest.generate(model, acceptance / "generated", manifest)
    selftest.compile_rtl(manifest, "verilator")
    selftest.behavior_rtl(manifest, "verilator")
    selftest.consistency(manifest)
    arguments = _arguments(tmp_path)
    _call(arguments)
    return arguments


@pytest.mark.parametrize("failure_point", ["command", "payload", "tree_rename", "report_rename", "final_validation"])
def test_failed_capability_publish_preserves_complete_prior_bundle(
    published_bundle: dict[str, Path], monkeypatch: pytest.MonkeyPatch, failure_point: str
) -> None:
    arguments = published_bundle
    final = arguments["secondary_output_dir"] / "evidence_v1"
    report = arguments["capability_report"]
    old_tree = _digest_tree(final)
    old_report = report.read_bytes()

    if failure_point == "command":
        monkeypatch.setattr(
            selftest, "_capability_command", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("injected command failure"))
        )
    elif failure_point == "payload":
        monkeypatch.setattr(
            selftest, "_validate_capability_payload", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("injected payload failure"))
        )
    elif failure_point == "final_validation":
        monkeypatch.setattr(
            selftest, "_validate_capability_final_payload", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("injected final validation failure"))
        )
    else:
        original = selftest._publish_replace
        target = final if failure_point == "tree_rename" else report
        seen = False

        def fail_once(source: Path, destination: Path) -> None:
            nonlocal seen
            if destination == target and not seen:
                seen = True
                raise OSError(f"injected {failure_point} failure")
            original(source, destination)

        monkeypatch.setattr(selftest, "_publish_replace", fail_once)

    with pytest.raises((OSError, RuntimeError, selftest.RuntimeConfigurationError), match="injected"):
        _call(arguments)

    assert _digest_tree(final) == old_tree
    assert report.read_bytes() == old_report
    assert not list(arguments["secondary_output_dir"].glob(".evidence_v1.backup-*"))


def _walk(value: object):
    if isinstance(value, dict):
        yield value
        for item in value.values():
            yield from _walk(item)
    elif isinstance(value, list):
        for item in value:
            yield from _walk(item)


def test_capability_rerun_rebases_paths_and_is_tree_deterministic(
    published_bundle: dict[str, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    arguments = published_bundle
    final = arguments["secondary_output_dir"] / "evidence_v1"
    report = arguments["capability_report"]
    before_tree = _digest_tree(final)
    before_report = report.read_bytes()
    monkeypatch.setattr(global_values, "key", 24681357)
    caller_json_key = global_values.key

    _call(arguments)

    assert global_values.key == caller_json_key
    assert _digest_tree(final) == before_tree
    assert report.read_bytes() == before_report
    stage_marker = ".evidence_v1.stage-"
    assert not list(arguments["secondary_output_dir"].glob(".evidence_v1.*"))
    for path in final.rglob("*"):
        if path.is_file() and not path.is_symlink():
            assert stage_marker not in path.read_text(encoding="utf-8", errors="replace")
    payload = json.loads(report.read_text(encoding="utf-8"))
    for item in _walk(payload):
        path = item.get("path")
        if isinstance(path, str):
            assert stage_marker not in path
            assert Path(path).exists()
        if {"path", "sha256", "size_bytes"} <= set(item):
            evidence = Path(item["path"])
            assert item["size_bytes"] == evidence.stat().st_size
            assert item["sha256"] == hashlib.sha256(evidence.read_bytes()).hexdigest()
    for nested_manifest in final.rglob("manifest.json"):
        selftest.inventory(nested_manifest)
