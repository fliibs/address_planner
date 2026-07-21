import hashlib
import json
from pathlib import Path

import pytest

from address_planner import AddressSpace, Field, RegSpace, Register
from address_planner.selftest import ManifestValidationError, consistency, generate


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _model() -> dict:
    return {
        "schema_version": 1,
        "model_id": "consistency_fixture",
        "name": "consistency_bank",
        "description": "cross-output fixture",
        "size_bytes": 256,
        "bus_width": 32,
        "software_interface": "apb",
        "registers": [
            {
                "name": "control",
                "offset_bytes": 0,
                "width_bits": 32,
                "fields": [
                    {"name": "enable", "lsb": 0, "width_bits": 1, "sw_access": "RW", "hw_access": "RO", "reset": 1},
                    {"name": "mode", "lsb": 4, "width_bits": 3, "sw_access": "RW", "hw_access": "RO", "reset": 2},
                ],
            },
            {
                "name": "status",
                "offset_bytes": 4,
                "width_bits": 32,
                "fields": [
                    {"name": "ready", "lsb": 0, "width_bits": 1, "sw_access": "RO", "hw_access": "RW", "reset": 0}
                ],
            },
            {
                "name": "events",
                "offset_bytes": 8,
                "width_bits": 32,
                "fields": [
                    {"name": "pending", "lsb": 0, "width_bits": 4, "sw_access": "W1C", "hw_access": "RW", "reset": 10}
                ],
            },
        ],
    }


def _generated(tmp_path: Path) -> Path:
    model = tmp_path / "model.json"
    model.write_text(json.dumps(_model()), encoding="utf-8")
    manifest = tmp_path / "manifest.json"
    generate(model, tmp_path / "generated", manifest)
    return manifest


def test_consistency_valid_is_deterministic_and_reports_explicit_coverage(tmp_path):
    manifest = _generated(tmp_path)
    first = consistency(manifest)
    second = consistency(manifest)
    report = json.loads(Path(first["report"]).read_text(encoding="utf-8"))

    assert first["sha256"] == second["sha256"]
    assert report["result"] == "pass"
    representations = {entry["class"]: entry for entry in report["representations"]}
    assert representations["c_header"]["not_represented"] == ["sw_access", "hw_access"]
    assert representations["register_rtl"]["inferred"] == ["sw_access", "hw_access"]


def test_consistency_rejects_tampered_artifact_without_changing_inputs(tmp_path):
    manifest = _generated(tmp_path)
    raw = json.loads(manifest.read_text(encoding="utf-8"))
    json_artifact = tmp_path / next(item["path"] for item in raw["artifacts"] if item["class"] == "json")
    json_artifact.write_text("[]\n", encoding="utf-8")
    before = {"manifest": _digest(manifest), "json": _digest(json_artifact)}

    with pytest.raises(ManifestValidationError, match="mismatch"):
        consistency(manifest)

    assert {"manifest": _digest(manifest), "json": _digest(json_artifact)} == before


def test_json_register_addresses_include_parent_byte_base_and_filled_fields_use_register_width():
    top = AddressSpace("top", 0x1000)
    bank = RegSpace("bank", 0x100, bus_width=32)
    status = Register("status", bit=32)
    status.add(Field("ready", 1), 0)
    bank.add(status, 4)
    top.add(bank, 0x100)
    nested_status = top.sub_space_list[0].sub_space_list[0]

    assert nested_status.report_json_core()["start_addr"] == "0x104"
    assert nested_status.report_json_core()["end_addr"] == "0x107"

    narrow = Register("narrow", bit=16)
    narrow.add(Field("data", 2), 1)
    assert [(field.name, field.bit_offset, field.bit) for field in narrow.filled_field_list] == [
        ("FilledField", 0, 1),
        ("data", 1, 2),
        ("FilledField", 3, 13),
    ]
    empty = Register("empty", bit=48)
    assert [(field.name, field.bit_offset, field.bit) for field in empty.filled_field_list] == [
        ("FilledField", 0, 48)
    ]
