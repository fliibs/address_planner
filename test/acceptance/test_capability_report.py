import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

from address_planner.selftest import (
    ModelValidationError,
    RuntimeConfigurationError,
    _bus_protocol_evidence,
    _capability_model,
    _validate_capability_payload,
    generate,
)


def _payload(path: Path) -> dict:
    return {
        "schema_version": 1,
        "evidence": {"path": str(path)},
        "capabilities": [
            {"id": "retain", "status": "pass", "evidence": [{"kind": "command", "path": str(path)}]},
            {"id": "optional", "status": "observed_nonmandatory", "reason": "baseline disposition"},
        ],
    }


def test_capability_report_validator_rejects_missing_rows_and_missing_evidence(tmp_path: Path) -> None:
    evidence = tmp_path / "evidence.json"
    evidence.write_text("{}\n", encoding="utf-8")
    valid = _payload(evidence)
    _validate_capability_payload(valid, ["retain"], ["optional"])

    missing_row = _payload(evidence)
    missing_row["capabilities"] = missing_row["capabilities"][:1]
    with pytest.raises(RuntimeConfigurationError, match="ID set"):
        _validate_capability_payload(missing_row, ["retain"], ["optional"])

    tampered = _payload(evidence)
    evidence.unlink()
    with pytest.raises(RuntimeConfigurationError, match="missing evidence"):
        _validate_capability_payload(tampered, ["retain"], ["optional"])


def test_aggregate_headers_are_stable_across_python_hash_seeds(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    model = {
        "schema_version": 1, "model_id": "stable_headers", "name": "stable_headers",
        "description": "deterministic aggregate headers", "size_bytes": 64, "bus_width": 32,
        "software_interface": "apb", "registers": [
            {"name": "control", "offset_bytes": 0, "width_bits": 32, "fields": [{"name": "enable", "lsb": 0, "width_bits": 1, "sw_access": "RW", "hw_access": "RO", "reset": 0}]},
            {"name": "status", "offset_bytes": 4, "width_bits": 32, "fields": [{"name": "ready", "lsb": 0, "width_bits": 1, "sw_access": "RO", "hw_access": "RW", "reset": 0}]},
        ],
    }
    model_path, manifest, output = tmp_path / "model.json", tmp_path / "manifest.json", tmp_path / "out"
    model_path.write_text(json.dumps(model), encoding="utf-8")
    command = [sys.executable, "-m", "address_planner.selftest", "generate", "--model-definition", str(model_path), "--output-dir", str(output), "--manifest", str(manifest)]
    environment = os.environ.copy()
    environment.update({"ADDRESS_PLANNER_ROOT": str(root), "UHDL_ROOT": str(root.parent / "uhdl")})
    environment.pop("PYTHONHOME", None)
    environment.pop("PYTHONPATH", None)
    digests = []
    for seed in ("1", "2"):
        environment["PYTHONHASHSEED"] = seed
        completed = subprocess.run(command, text=True, capture_output=True, env=environment, check=False)
        assert completed.returncode == 0, completed.stderr
        aggregate = output / "stable_headers" / "chead" / "all.h"
        aggregate_vh = output / "stable_headers" / "vhead" / "all.vh"
        digests.append((hashlib.sha256(aggregate.read_bytes()).hexdigest(), hashlib.sha256(aggregate_vh.read_bytes()).hexdigest()))
    assert digests[0] == digests[1]


def test_canonical_json_accepts_all_supported_interfaces_and_distinguishes_protocols(
    tmp_path: Path,
) -> None:
    expected = {
        "apb3": ("apb", {"base_apb_ports", "no_p_strb", "no_p_prot"}),
        "apb4": ("apb4", {"base_apb_ports", "p_strb_4_bits", "p_prot_3_bits"}),
        "valid_ready": ("vr", {"valid_ready_ports", "no_apb_ports"}),
    }
    for bus_id, (interface, checks) in expected.items():
        model = tmp_path / f"{bus_id}.json"
        manifest = tmp_path / bus_id / "manifest.json"
        model.write_text(json.dumps(_capability_model(f"bus_{bus_id}", interface)), encoding="utf-8")
        generate(model, manifest.parent / "generated", manifest)
        assert manifest.is_file()
        report = _bus_protocol_evidence(bus_id, interface, manifest, tmp_path)
        payload = json.loads(Path(report["path"]).read_text(encoding="utf-8"))
        assert set(payload["checks"]) == checks
        assert all(payload["checks"].values())


@pytest.mark.parametrize("software_interface", ["unknown", "APB", "APB4", "VR"])
def test_canonical_json_rejects_unknown_or_case_variant_interfaces_before_publication(
    tmp_path: Path, software_interface: str
) -> None:
    model = _capability_model("invalid_interface", "apb")
    model["software_interface"] = software_interface
    model_path = tmp_path / "model.json"
    output_dir = tmp_path / "generated"
    manifest = tmp_path / "delivery_manifest.json"
    model_path.write_text(json.dumps(model), encoding="utf-8")

    with pytest.raises(ModelValidationError, match=rf"model\.software_interface.*{software_interface!r}"):
        generate(model_path, output_dir, manifest)

    assert not output_dir.exists()
    assert not manifest.exists()


@pytest.mark.parametrize("bus_width", [8, 16, 64])
def test_canonical_json_rejects_non_32_bit_bus_width_before_publication(
    tmp_path: Path, bus_width: int
) -> None:
    model = _capability_model("invalid_bus_width", "apb")
    model["bus_width"] = bus_width
    model["registers"][0]["width_bits"] = bus_width
    model_path = tmp_path / "model.json"
    output_dir = tmp_path / "generated"
    manifest = tmp_path / "delivery_manifest.json"
    model_path.write_text(json.dumps(model), encoding="utf-8")

    with pytest.raises(ModelValidationError, match=rf"model\.bus_width.*{bus_width}"):
        generate(model_path, output_dir, manifest)

    assert not output_dir.exists()
    assert not manifest.exists()
