"""Regression checks for intranet RALF compatibility and diagnostics."""

from __future__ import annotations

import importlib
from pathlib import Path
from tkinter import Tcl, TclError

import pytest

from address_planner import AddressSpace, MB
from address_planner.ralf_parser.ralf_parse import (
    RalfNumericParseError,
    RalfParseError,
    convert_address,
    convert_address_with_context,
)


@pytest.mark.parametrize(
    ("literal", "expected"),
    [
        ("@0xfb4", 0xFB4),
        ("@0xb10", 0xB10),
        ("@0x800", 0x800),
        ("@'h0x20000", 0x20000),
        ("@'H0Xb000", 0xB000),
        ("32'h0x2_0000", 0x20000),
        ("@'h0x0000", 0),
        ("@0b100", 4),
        ("32'h1_000", 0x1000),
        ("16b1010", 10),
        ("d384", 384),
    ],
)
def test_convert_address_supported_literals(literal: str, expected: int) -> None:
    assert convert_address(literal) == expected


@pytest.mark.parametrize("literal", ["@'h0x", "@'h0xZZ", "bad'h0x100", "@'b102"])
def test_malformed_literals_are_not_silently_accepted(literal):
    with pytest.raises(ValueError):
        convert_address(literal)


def test_system_block_instances_with_combined_hex_prefix(tmp_path):
    source = tmp_path / "dma.ralf"
    source.write_text("""
register ctrl { bytes 4;
    field enable @0 { bits 1; access rw; reset 1; }
}
block common { register ctrl @0; }
block ch1 { register ctrl @0; }
block ch2 { register ctrl @0; }
system peri_dma {
    bytes 8;
    block common @'h0x20000;
    block ch1 @'h0x0000;
    block ch2 @'H0X1000;
}
""")
    model = AddressSpace("soc", MB).add_ralf(source, 0)
    assert [child.offset for child in model.sub_space_list] == [0x20000, 0, 0x1000]
    assert len({id(child) for child in model.sub_space_list}) == 3
    for bank in model.sub_space_list:
        assert bank.father is model
        assert bank.sub_space_list[0].father is bank
    first, second, _ = model.sub_space_list
    first.sub_space_list[0].field_list[0].init_value = 0
    assert second.sub_space_list[0].field_list[0].init_value == 1


def test_recursive_helpers_preserve_caller_tree():
    from address_planner import RegSpace, Register, Field, ReadWrite
    from address_planner.ralf_parser.ralf_parse import (
        build_subspace_recur, build_field_recur, minimum_size,
    )
    bank = RegSpace("existing", 4096)
    register = Register("r", bit=32)
    register.add(Field("value", bit=1, sw_access=ReadWrite, init_value=0), 0)
    bank.add(register, 0)
    cloned = build_subspace_recur({}, bank, None)
    assert bank.size == 4096
    assert cloned is not bank
    assert cloned.sub_space_list[0].father is cloned
    cloned.sub_space_list[0].field_list[0].init_value = 1
    assert bank.sub_space_list[0].field_list[0].init_value == 0
    field_clone = build_field_recur({}, register, None)
    field_clone.field_list[0].init_value = 1
    assert register.field_list[0].init_value == 0
    resized = minimum_size(bank)
    assert resized.size == 4 and bank.size == 4096


def test_convert_address_error_retains_raw_value_and_hierarchy() -> None:
    with pytest.raises(RalfNumericParseError) as caught:
        convert_address_with_context("@0xnot_hex", "$DEF(top) ADDR_DICT bad addr")

    assert caught.value.raw_value == "@0xnot_hex"
    assert caught.value.hierarchy == "$DEF(top) ADDR_DICT bad addr"


@pytest.mark.parametrize(
    ("literal", "expected_bytes"),
    [("@0xfb4", 0xFB4), ("@0xb10", 0xB10), ("@'h0x20000", 0x20000)],
)
def test_standard_prefixes_survive_real_ralf_import(
    tmp_path: Path, literal: str, expected_bytes: int
) -> None:
    project_root = Path(__file__).resolve().parents[2]
    fixture = project_root / "address_planner" / "ralf_parser" / "test.ralf"
    source = fixture.read_text(encoding="utf-8")
    modified = source.replace(
        "register L1 @1 {",
        f"register L1 {literal} {{",
        1,
    )
    ralf_path = tmp_path / "prefix_regression.ralf"
    ralf_path.write_text(modified, encoding="utf-8")

    imported = AddressSpace("parent", 64 * MB).add_ralf(ralf_path, 0, "imported")
    block_b1 = next(
        child for child in imported.sub_space_list if child.module_name == "B1"
    )
    register_l1 = next(
        child for child in block_b1.sub_space_list if child.module_name == "L1"
    )

    # Register offsets are stored as bits inside the address model.
    assert register_l1.offset // 8 == expected_bytes


class _SuccessfulTcl:
    def call(self, *_args):
        return None

    def eval(self, _code):
        return None


def _patch_successful_import(monkeypatch: pytest.MonkeyPatch) -> None:
    module = importlib.import_module("address_planner.AddressSpace")
    monkeypatch.setattr(module, "Tcl", _SuccessfulTcl)
    monkeypatch.setattr(module, "build_addrspace", lambda _interpreter: AddressSpace("ralf", 4))


def test_add_ralf_accepts_legacy_and_current_keywords(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    _patch_successful_import(monkeypatch)
    ralf_path = tmp_path / "input.ralf"
    ralf_path.write_text("block dummy {}\n", encoding="utf-8")

    legacy_parent = AddressSpace("legacy_parent", 16)
    current_parent = AddressSpace("current_parent", 16)

    legacy = legacy_parent.add_ralf(sub_space=ralf_path, offset=0, name="instance")
    current = current_parent.add_ralf(ralf_file=ralf_path, offset=0, name="instance")

    assert legacy.module_name == current.module_name == "ralf"
    assert legacy_parent.sub_space_list[0].module_name == "instance"
    assert current_parent.sub_space_list[0].module_name == "instance"


def test_add_ralf_rejects_ambiguous_keywords(tmp_path: Path) -> None:
    ralf_path = tmp_path / "input.ralf"
    ralf_path.write_text("block dummy {}\n", encoding="utf-8")

    with pytest.raises(TypeError, match="either 'ralf_file' or legacy 'sub_space'"):
        AddressSpace("parent", 16).add_ralf(
            ralf_file=ralf_path,
            sub_space=ralf_path,
            offset=0,
        )


def test_add_ralf_tcl_error_reports_input_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    module = importlib.import_module("address_planner.AddressSpace")

    class _FailingTcl:
        def call(self, *_args):
            return None

        def eval(self, code):
            if code == 'set ::errorInfo':
                return 'variable DEF(reserved_field) not found'
            raise TclError('variable DEF(reserved_field) not found')

    monkeypatch.setattr(module, "Tcl", _FailingTcl)
    ralf_path = tmp_path / "broken.ralf"
    ralf_path.write_text("use $DEF(reserved_field)\n", encoding="utf-8")

    with pytest.raises(RalfParseError) as caught:
        AddressSpace("parent", 16).add_ralf(ralf_path, 0)

    message = str(caught.value)
    assert str(ralf_path.resolve()) in message
    assert "DEF(reserved_field)" in message


def test_undefined_reserved_field_instance_is_skipped_case_insensitively() -> None:
    project_root = Path(__file__).resolve().parents[2]
    parser_tcl = project_root / "address_planner" / "ralf_parser" / "ralf_parser.tcl"
    interpreter = Tcl()
    interpreter.call("source", str(parser_tcl))
    interpreter.eval("set FIELD_DICT [dict create]")

    interpreter.eval("field reserved @0")
    interpreter.eval("field RESERVED @4")

    assert interpreter.eval("dict size $FIELD_DICT") == "0"


def test_reserved_guard_does_not_hide_other_missing_definitions() -> None:
    project_root = Path(__file__).resolve().parents[2]
    parser_tcl = project_root / "address_planner" / "ralf_parser" / "ralf_parser.tcl"
    interpreter = Tcl()
    interpreter.call("source", str(parser_tcl))
    interpreter.eval("set FIELD_DICT [dict create]")

    with pytest.raises(TclError, match="Variable DEF\\(missing.field\\) not found"):
        interpreter.eval("field missing @0")


def test_defined_reserved_field_is_still_imported() -> None:
    project_root = Path(__file__).resolve().parents[2]
    parser_tcl = project_root / "address_planner" / "ralf_parser" / "ralf_parser.tcl"
    interpreter = Tcl()
    interpreter.call("source", str(parser_tcl))
    interpreter.eval("set FIELD_DICT [dict create]")

    interpreter.eval("field reserved @4 { bits 1; access ro; reset 0; }")

    assert interpreter.eval("dict exists $FIELD_DICT reserved.field") == "1"


def test_add_ralf_numeric_error_reports_candidate_line(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    module = importlib.import_module("address_planner.AddressSpace")
    monkeypatch.setattr(module, "Tcl", _SuccessfulTcl)

    def _fail_numeric(_interpreter):
        raise RalfNumericParseError("@0xnot_hex", "$DEF(top) ADDR_DICT bad addr")

    monkeypatch.setattr(module, "build_addrspace", _fail_numeric)
    ralf_path = tmp_path / "bad_numeric.ralf"
    ralf_path.write_text(
        "block top {\n  register bad @0xnot_hex {\n  }\n}\n",
        encoding="utf-8",
    )

    with pytest.raises(RalfParseError) as caught:
        AddressSpace("parent", 16).add_ralf(ralf_path, 0)

    message = str(caught.value)
    assert str(ralf_path.resolve()) in message
    assert "numeric value='@0xnot_hex'" in message
    assert "candidate lines=2" in message


def test_intranet_modulefile_template_enforces_project_roots() -> None:
    project_root = Path(__file__).resolve().parents[2]
    template = (
        project_root / "config" / "modulefiles" / "addr_planner" / "v3p0.in"
    ).read_text(encoding="utf-8")

    assert "module load $uhdl_module" in template
    assert "module load UHDL" not in template
    assert "address_planner _runtime.py" in template
    assert "$env(UHDL_ROOT) uhdl __init__.py" in template
    assert "module use /tools/modules-4.0" not in template
