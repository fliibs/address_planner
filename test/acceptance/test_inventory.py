"""Focused read-only tests for the delivery-manifest inventory command."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

from address_planner.selftest import (
    ManifestValidationError,
    _preserved_verification_records,
    behavior_rtl,
    compile_rtl,
    inventory,
    main,
)


REQUIRED_CLASSES = ("register_rtl", "c_header", "verilog_header", "ralf", "json")


def _record(kind: str, path: Path, manifest_parent: Path) -> dict[str, object]:
    return {
        "class": kind,
        "status": "generated",
        "path": path.relative_to(manifest_parent).as_posix(),
        "size_bytes": path.stat().st_size,
        "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


def _manifest(tmp_path: Path) -> tuple[Path, dict[str, object], dict[str, Path]]:
    output_root = tmp_path / "generated"
    output_root.mkdir()
    files: dict[str, Path] = {}
    for kind in REQUIRED_CLASSES:
        path = output_root / f"{kind}.txt"
        path.write_text(f"{kind} output\n", encoding="utf-8")
        files[kind] = path
    manifest_path = tmp_path / "delivery_manifest.json"
    payload: dict[str, object] = {
        "schema_version": 1,
        "model": {"id": "unit", "path": "model.json", "sha256": "0" * 64},
        "runtime": {},
        "output_root": "generated",
        "artifacts": [_record(kind, files[kind], tmp_path) for kind in REQUIRED_CLASSES],
        "auxiliary_artifacts": [],
        "verification_records": [],
    }
    manifest_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return manifest_path, payload, files


def _write(manifest_path: Path, payload: dict[str, object]) -> None:
    manifest_path.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")


def test_inventory_accepts_valid_manifest_without_rewriting(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    manifest_path, _payload, files = _manifest(tmp_path)
    before = {path: path.read_bytes() for path in [manifest_path, *files.values()]}

    result = inventory(manifest_path)

    assert result["artifact_count"] == len(REQUIRED_CLASSES)
    assert result["required_classes"] == list(REQUIRED_CLASSES)
    assert {path: path.read_bytes() for path in before} == before
    assert main(["inventory", "--manifest", str(manifest_path)]) == 0
    assert json.loads(capsys.readouterr().out)["artifact_count"] == len(REQUIRED_CLASSES)
    assert {path: path.read_bytes() for path in before} == before


def test_inventory_rejects_tampered_required_artifact(tmp_path: Path) -> None:
    manifest_path, _payload, files = _manifest(tmp_path)
    files["json"].write_text("tampered\n", encoding="utf-8")

    with pytest.raises(ManifestValidationError, match="size_bytes mismatch|sha256 mismatch"):
        inventory(manifest_path)


def test_inventory_rejects_missing_required_artifact(tmp_path: Path) -> None:
    manifest_path, _payload, files = _manifest(tmp_path)
    files["ralf"].unlink()

    with pytest.raises(ManifestValidationError, match="escapes the manifest directory or cannot be resolved"):
        inventory(manifest_path)


def test_inventory_rejects_malformed_json(tmp_path: Path) -> None:
    manifest_path, _payload, _files = _manifest(tmp_path)
    manifest_path.write_text("{invalid json", encoding="utf-8")

    with pytest.raises(ManifestValidationError, match="not valid JSON"):
        inventory(manifest_path)


def test_inventory_rejects_duplicate_required_class(tmp_path: Path) -> None:
    manifest_path, payload, _files = _manifest(tmp_path)
    artifacts = list(payload["artifacts"])
    artifacts[-1] = dict(artifacts[0])
    payload["artifacts"] = artifacts
    _write(manifest_path, payload)

    with pytest.raises(ManifestValidationError, match="duplicates another artifact path"):
        inventory(manifest_path)


def test_inventory_rejects_path_escape(tmp_path: Path) -> None:
    manifest_path, payload, _files = _manifest(tmp_path)
    artifacts = list(payload["artifacts"])
    escaped = dict(artifacts[0])
    escaped["path"] = "../outside.txt"
    artifacts[0] = escaped
    payload["artifacts"] = artifacts
    _write(manifest_path, payload)

    with pytest.raises(ManifestValidationError, match="must be relative and must not contain '..'"):
        inventory(manifest_path)


def test_inventory_rejects_symlink_outside_manifest_parent(tmp_path: Path) -> None:
    manifest_path, payload, files = _manifest(tmp_path)
    outside = tmp_path.parent / "outside.txt"
    outside.write_text("outside\n", encoding="utf-8")
    escaped_link = files["c_header"].with_name("escape-link.txt")
    os.symlink(outside, escaped_link)
    artifacts = list(payload["artifacts"])
    replacement = dict(artifacts[1])
    replacement["path"] = escaped_link.relative_to(tmp_path).as_posix()
    replacement["size_bytes"] = outside.stat().st_size
    replacement["sha256"] = hashlib.sha256(outside.read_bytes()).hexdigest()
    artifacts[1] = replacement
    payload["artifacts"] = artifacts
    _write(manifest_path, payload)

    with pytest.raises(ManifestValidationError, match="escapes the manifest directory or cannot be resolved"):
        inventory(manifest_path)


def test_inventory_validates_auxiliary_records(tmp_path: Path) -> None:
    manifest_path, payload, files = _manifest(tmp_path)
    payload["auxiliary_artifacts"] = [_record("filelist", files["register_rtl"], tmp_path)]
    _write(manifest_path, payload)

    with pytest.raises(ManifestValidationError, match="duplicates another artifact path"):
        inventory(manifest_path)


def _strict_fake_verilator(tmp_path: Path) -> Path:
    tool = tmp_path / "fake_verilator"
    tool.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"--version\" ]; then echo 'Fake Verilator 1.0'; exit 0; fi\n"
        "if [ \"$1\" = \"--lint-only\" ] && [ \"$2\" = \"-Wall\" ] && [ \"$3\" = \"-f\" ] && [ -n \"$4\" ] && [ \"$#\" = 4 ]; then\n"
        "  echo strict-lint-pass; exit 0\n"
        "fi\n"
        "echo invalid-argv >&2; exit 9\n",
        encoding="utf-8",
    )
    tool.chmod(0o755)
    return tool


def test_compile_records_strict_command_and_inventory_validates_log(tmp_path: Path) -> None:
    manifest_path, payload, files = _manifest(tmp_path)
    filelist = files["register_rtl"].with_name("filelist.f")
    filelist.write_text(f"{files['register_rtl']}\n", encoding="utf-8")
    payload["auxiliary_artifacts"] = [_record("filelist", filelist, tmp_path)]
    _write(manifest_path, payload)

    result = compile_rtl(manifest_path, str(_strict_fake_verilator(tmp_path)))

    stored = json.loads(manifest_path.read_text(encoding="utf-8"))
    record = stored["verification_records"]
    assert result["exit_code"] == 0
    assert len(record) == 1
    assert record[0]["argv"][1:4] == ["--lint-only", "-Wall", "-f"]
    assert "-Wno-" not in " ".join(record[0]["argv"])
    assert inventory(manifest_path)["verification_record_count"] == 1


def test_inventory_rejects_tampered_verification_log(tmp_path: Path) -> None:
    manifest_path, payload, files = _manifest(tmp_path)
    filelist = files["register_rtl"].with_name("filelist.f")
    filelist.write_text(f"{files['register_rtl']}\n", encoding="utf-8")
    payload["auxiliary_artifacts"] = [_record("filelist", filelist, tmp_path)]
    _write(manifest_path, payload)
    compile_rtl(manifest_path, str(_strict_fake_verilator(tmp_path)))
    stored = json.loads(manifest_path.read_text(encoding="utf-8"))
    log_path = tmp_path / stored["verification_records"][0]["log"]["path"]
    log_path.write_text("tampered\n", encoding="utf-8")

    with pytest.raises(ManifestValidationError, match="log size or SHA-256 mismatch"):
        inventory(manifest_path)


def test_inventory_rejects_tampered_verification_record(tmp_path: Path) -> None:
    manifest_path, payload, files = _manifest(tmp_path)
    filelist = files["register_rtl"].with_name("filelist.f")
    filelist.write_text(f"{files['register_rtl']}\n", encoding="utf-8")
    payload["auxiliary_artifacts"] = [_record("filelist", filelist, tmp_path)]
    _write(manifest_path, payload)
    compile_rtl(manifest_path, str(_strict_fake_verilator(tmp_path)))
    stored = json.loads(manifest_path.read_text(encoding="utf-8"))
    stored["verification_records"][0]["inputs"]["model_sha256"] = "f" * 64
    _write(manifest_path, stored)

    with pytest.raises(ManifestValidationError, match="does not match the manifest model"):
        inventory(manifest_path)


def test_generation_preservation_filters_invalid_verification_evidence(tmp_path: Path) -> None:
    manifest_path, payload, files = _manifest(tmp_path)
    filelist = files["register_rtl"].with_name("filelist.f")
    filelist.write_text(f"{files['register_rtl']}\n", encoding="utf-8")
    payload["auxiliary_artifacts"] = [_record("filelist", filelist, tmp_path)]
    _write(manifest_path, payload)
    compile_rtl(manifest_path, str(_strict_fake_verilator(tmp_path)))
    stored = json.loads(manifest_path.read_text(encoding="utf-8"))
    preserved = _preserved_verification_records(
        manifest_path,
        output_root=tmp_path / stored["output_root"],
        model_sha256=stored["model"]["sha256"],
        artifacts=stored["artifacts"],
    )
    assert preserved == stored["verification_records"]
    changed_artifacts = [dict(record) for record in stored["artifacts"]]
    changed_artifacts[0]["sha256"] = "f" * 64
    assert _preserved_verification_records(
        manifest_path,
        output_root=tmp_path / stored["output_root"],
        model_sha256=stored["model"]["sha256"],
        artifacts=changed_artifacts,
    ) == []
    log_path = tmp_path / stored["verification_records"][0]["log"]["path"]
    log_path.write_text("invalidated\n", encoding="utf-8")
    assert _preserved_verification_records(
        manifest_path,
        output_root=tmp_path / stored["output_root"],
        model_sha256=stored["model"]["sha256"],
        artifacts=stored["artifacts"],
    ) == []


def _behavior_manifest(tmp_path: Path) -> Path:
    manifest_path, payload, files = _manifest(tmp_path)
    rtl = files["register_rtl"]
    rtl.write_text("module Regbank_cfg_RegSpace0 (); endmodule\n", encoding="utf-8")
    filelist = rtl.with_name("filelist.f")
    filelist.write_text(f"{rtl}\n", encoding="utf-8")
    fixture = Path(__file__).resolve().parents[1] / "fixtures" / "representative_register_model.json"
    payload["model"] = {
        "id": "representative_register_model",
        "path": str(fixture),
        "sha256": hashlib.sha256(fixture.read_bytes()).hexdigest(),
    }
    artifacts = list(payload["artifacts"])
    artifacts[0] = _record("register_rtl", rtl, tmp_path)
    payload["artifacts"] = artifacts
    payload["auxiliary_artifacts"] = [_record("filelist", filelist, tmp_path)]
    _write(manifest_path, payload)
    return manifest_path


def _behavior_fake_verilator(tmp_path: Path, *, compile_exit: int) -> Path:
    tool = tmp_path / "fake_behavior_verilator"
    tool.write_text(
        "#!/bin/sh\n"
        "if [ \"$1\" = \"--version\" ]; then echo 'Fake Verilator behavior 1.0'; exit 0; fi\n"
        f"if [ {compile_exit} -ne 0 ]; then echo compile-fail; exit {compile_exit}; fi\n"
        "while [ $# -gt 0 ]; do\n"
        "  if [ \"$1\" = \"--Mdir\" ]; then work=$2; shift 2; continue; fi\n"
        "  shift\n"
        "done\n"
        "mkdir -p \"$work\"\n"
        "printf '#!/bin/sh\\necho OBSERVATION PASS fake-behavior\\nexit 0\\n' > \"$work/Vaddress_planner_behavior_tb\"\n"
        "chmod +x \"$work/Vaddress_planner_behavior_tb\"\n"
        "echo compile-pass\n",
        encoding="utf-8",
    )
    tool.chmod(0o755)
    return tool


def test_behavior_failure_does_not_publish_success_record(tmp_path: Path) -> None:
    manifest_path = _behavior_manifest(tmp_path)
    result = behavior_rtl(manifest_path, str(_behavior_fake_verilator(tmp_path, compile_exit=17)))

    assert result["compile_exit_code"] == 17
    stored = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert stored["verification_records"] == []


def test_behavior_supporting_evidence_is_validated_and_invalidated(tmp_path: Path) -> None:
    manifest_path = _behavior_manifest(tmp_path)
    result = behavior_rtl(manifest_path, str(_behavior_fake_verilator(tmp_path, compile_exit=0)))

    assert result["compile_exit_code"] == 0
    assert result["run_exit_code"] == 0
    stored = json.loads(manifest_path.read_text(encoding="utf-8"))
    record = stored["verification_records"][0]
    assert record["kind"] == "register_behavior"
    assert inventory(manifest_path)["verification_record_count"] == 1
    testbench = tmp_path / record["supporting_artifacts"][0]["path"]
    testbench.write_text("tampered\n", encoding="utf-8")
    with pytest.raises(ManifestValidationError, match="size_bytes mismatch|sha256 mismatch"):
        inventory(manifest_path)
    assert _preserved_verification_records(
        manifest_path,
        output_root=tmp_path / stored["output_root"],
        model_sha256=stored["model"]["sha256"],
        artifacts=stored["artifacts"],
    ) == []
