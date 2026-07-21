"""Fixture-driven checks required by the sealed A02 acceptance contract."""

from __future__ import annotations

import inspect
import json
import os
from pathlib import Path

import pytest

from address_planner import (
    AddressSpace,
    Field,
    ReadOnly,
    ReadWrite,
    RegSpace,
    Register,
    Write1Clean,
)
import address_planner
import uhdl


EXPECTED_NEGATIVE_CASES = {
    "address_overlap",
    "register_misalignment",
    "field_overlap",
    "invalid_access_type",
    "reset_value_too_wide",
    "non_positive_width",
    "array_out_of_range",
}


def _fixture_path(variable: str) -> Path:
    value = os.environ.get(variable)
    assert value, f"{variable} must point to the sealed fixture"
    path = Path(value)
    assert path.is_file(), f"{variable} does not name a file: {path}"
    return path


@pytest.fixture(scope="module")
def representative_model() -> dict:
    return json.loads(_fixture_path("ADDRESS_PLANNER_MODEL_DEFINITION").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def negative_cases() -> list[dict]:
    data = json.loads(_fixture_path("ADDRESS_PLANNER_NEGATIVE_CASES").read_text(encoding="utf-8"))
    cases = data["cases"]
    assert {case["id"] for case in cases} == EXPECTED_NEGATIVE_CASES
    assert len(cases) == len(EXPECTED_NEGATIVE_CASES)
    return cases


def _access(value: str):
    return {"RW": ReadWrite, "RO": ReadOnly, "W1C": Write1Clean}[value]


def _build_model(model: dict) -> RegSpace:
    bank = RegSpace(
        model["name"],
        model["size_bytes"],
        software_interface=model["software_interface"],
        bus_width=model["bus_width"],
    )
    for register_spec in model["registers"]:
        register = Register(register_spec["name"], register_spec["width_bits"])
        for field_spec in register_spec["fields"]:
            register.add(
                Field(
                    field_spec["name"],
                    field_spec["width_bits"],
                    _access(field_spec["sw_access"]),
                    _access(field_spec["hw_access"]),
                    field_spec["reset"],
                ),
                field_spec["lsb"],
            )
        bank.add(register, register_spec["offset_bytes"], register_spec["name"])
    return bank


def test_fixture_model_generates_all_required_outputs(tmp_path: Path, representative_model: dict) -> None:
    bank = _build_model(representative_model)
    bank.generate(str(tmp_path))
    output_root = tmp_path / representative_model["name"]
    required = {
        "register_rtl": next((output_root / "rtl").rglob("*.v")),
        "c_header": output_root / "chead" / f"addr_{representative_model['name']}.h",
        "verilog_header": output_root / "vhead" / f"addr_{representative_model['name']}.vh",
        "ralf": output_root / "ralf" / f"{representative_model['name']}.ralf",
        "json": output_root / "html" / "data.json",
    }
    for artifact in required.values():
        assert artifact.is_file(), artifact
        assert artifact.stat().st_size > 0, artifact


def _negative_operation(case_id: str) -> None:
    if case_id == "address_overlap":
        bank = RegSpace("overlap", 64)
        bank.add(Register("first", 32), 0)
        bank.add(Register("second", 32), 0)
    elif case_id == "register_misalignment":
        RegSpace("alignment", 64).add(Register("reg", 32), 2)
    elif case_id == "field_overlap":
        register = Register("field_overlap", 32)
        register.add(Field("first", 2), 0)
        register.add(Field("second", 2), 1)
    elif case_id == "invalid_access_type":
        Field("bad_access", 1, sw_access="RW")
    elif case_id == "reset_value_too_wide":
        Field("bad_reset", 2, init_value=4)
    elif case_id == "non_positive_width":
        Field("zero_width", 0)
    elif case_id == "array_out_of_range":
        address_space = AddressSpace("address_array", 4)
        address_space.add(AddressSpace("element", 4), 2)
    else:  # pragma: no cover - set equality above makes this unreachable.
        raise AssertionError(f"unexpected negative fixture case: {case_id}")


@pytest.mark.parametrize("case_id", sorted(EXPECTED_NEGATIVE_CASES))
def test_fixed_negative_validation_cases(negative_cases: list[dict], case_id: str) -> None:
    expected = {case["id"]: case["expected_error"] for case in negative_cases}[case_id]
    with pytest.raises((ValueError, Exception), match=expected):
        _negative_operation(case_id)


def test_canonical_uhdl_provenance() -> None:
    canonical_root = Path(os.environ["UHDL_ROOT"]).resolve()
    legacy_root = Path(address_planner.__file__).resolve().parent / "uhdl"
    component_source = Path(inspect.getfile(address_planner.Component)).resolve()
    uhdl_source = Path(uhdl.__file__).resolve()
    runtime_root = Path(address_planner.__file__).resolve().parent
    assert component_source.is_relative_to(canonical_root)
    assert uhdl_source.is_relative_to(canonical_root)
    assert not component_source.is_relative_to(legacy_root)
    assert address_planner.Component is uhdl.Component
    forbidden_tokens = ("from .uhdl", "from ..uhdl", ".uhdl.uhdl")
    for source_path in runtime_root.rglob("*.py"):
        if "uhdl" in source_path.relative_to(runtime_root).parts:
            continue
        source = source_path.read_text(encoding="utf-8")
        assert not any(token in source for token in forbidden_tokens), source_path
