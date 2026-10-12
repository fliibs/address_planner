"""Regbank-local APB naming and two-argument UInt compatibility."""

import ast
import importlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from address_planner import (
    ExternalField, Field, Magic, Null, ReadOnly, ReadWrite,
    Register, RegSpace, Write0Pulse, Write1Pulse,
)

rtl_module = importlib.import_module("address_planner.RegSpaceRTL")


def make_bank(interface):
    bank = RegSpace("compat", 4096, software_interface=interface)
    first = Register("magic_before", reg_type=Magic)
    first.add_magic(password=0xA5)
    bank.add(first, 0)

    control = Register("control", parity=True)
    control.add(Field("value", 8, sw_access=ReadWrite, hw_access=ReadWrite), 0)
    bank.add(control, 0x20, magic_list=["magic_before", "magic_after"])

    external = Register("external")
    external.add(ExternalField("value", 8, sw_access=ReadWrite, hw_access=ReadWrite), 0)
    bank.add(external, 0x24)

    pulse = Register("pulse")
    pulse.add(Field("set", 1, sw_access=Write1Pulse, hw_access=ReadOnly), 0)
    pulse.add(Field("clear", 1, sw_access=Write0Pulse, hw_access=ReadOnly), 1)
    bank.add(pulse, 0x28, magic_list=["magic_after"])

    last = Register("magic_after", reg_type=Magic)
    last.add_magic(password=0x5A)
    bank.add(last, 0x30)
    return bank


def check_interface(interface, tmp_path):
    original_uint = rtl_module.UInt
    constants = []

    def two_argument_uint(width, value=0):
        assert isinstance(value, int)
        constants.append((width, value))
        return original_uint(width, value)

    # Reject a third argument even when the installed UHDL would accept it.
    with patch.object(rtl_module, "UInt", two_argument_uint):
        component = rtl_module.RegSpaceRTL(make_bank(interface)).u
    rtl = "\n".join(component.verilog_def)
    component.output_dir = str(tmp_path)
    component.generate_verilog(iteration=True)
    assert list(tmp_path.rglob("*.v"))
    names = {sig.name_before_component for sig in component.io_list}

    assert {(32, 0x20), (32, 0x24), (32, 0x28), (32, 0xA5),
            (32, 0x5A), (32, 2**32 - 2)} <= set(constants)
    assert "control_value_rdat" in names
    assert "parity_err_inject" in names
    if interface.startswith("apb"):
        expected = {"paddr", "psel", "penable", "pwrite", "pwdata",
                    "pready", "prdata", "pslverr"}
        if interface == "apb4":
            expected |= {"pstrb"}
            assert "p_mask" in rtl and "p_unmask" in rtl
            assert component.p.strb.width == 4
        assert not {"pprot", "p_prot"} & names
        assert not hasattr(component.p, "prot")
        assert expected <= names
        assert not any(name.startswith("p_") for name in names)
        assert component.p.addr is component.p_addr
    else:
        assert not hasattr(component, "p")
        assert "rreq_addr" in names and "rack_data" in names


def check_storage():
    bank = RegSpace("storage", 4096, software_interface="vr")
    register = Register("storage", parity=True)
    register.add(Field("value", 8, sw_access=Null, hw_access=ReadWrite), 0)
    bank.add(register, 0)
    component = rtl_module.RegSpaceRTL(bank).u
    assert not hasattr(component, "p")
    names = {sig.name_before_component for sig in component.io_list}
    assert {"storage_value_wdat", "storage_value_wena", "storage_value_rdat"} <= names
    assert "parity_err_inject" in names
    assert "storage_value" in "\n".join(component.verilog_def)


def check_uint_calls():
    tree = ast.parse(Path(rtl_module.__file__).read_text())
    calls = [node for node in ast.walk(tree) if isinstance(node, ast.Call)
             and isinstance(node.func, ast.Name) and node.func.id == "UInt"]
    assert calls
    assert all(len(node.args) <= 2 for node in calls)


class RegbankIntranetCompatTest(unittest.TestCase):
    def setUp(self):
        self.previous_dir = Path.cwd()
        self.temp_dir = tempfile.TemporaryDirectory(prefix="regbank_compat_")
        self.addCleanup(self.temp_dir.cleanup)
        self.addCleanup(os.chdir, self.previous_dir)
        os.chdir(self.temp_dir.name)

    def test_apb3(self):
        check_interface("apb", Path(self.temp_dir.name))

    def test_apb4(self):
        check_interface("apb4", Path(self.temp_dir.name))

    def test_valid_ready(self):
        check_interface("vr", Path(self.temp_dir.name))

    def test_storage_only(self):
        check_storage()

    def test_uint_calls(self):
        check_uint_calls()

    def test_apb4_reverse_keeps_strobes_without_prot(self):
        from address_planner.address_planner_rtl.APBInterface import APB4
        for width in (32, 64):
            forward = APB4(data_width=width)
            reverse = forward.reverse()
            assert forward.strb.width == reverse.strb.width == width // 8
            assert isinstance(forward.strb, rtl_module.Input)
            assert isinstance(reverse.strb, rtl_module.Output)
            assert not hasattr(forward, "prot")
            assert not hasattr(reverse, "prot")


if __name__ == "__main__":
    unittest.main()
