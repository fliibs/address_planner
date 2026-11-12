"""Protocol/CLI tests, not substitutes for the separately retained real EDA runs."""

import hashlib
import json
import os
from pathlib import Path
import signal
import sys

import pytest

import address_planner.selftest as selftest
from address_planner.selftest import RuntimeConfigurationError, main


VERILATOR_END = "- Verilator: Walltime 0.001 s (elab=0.001)\n"
VCS_END = "CPU time: .01 seconds to compile + .01 seconds to elab + .01 seconds to link\n"


def _fake(tmp_path: Path, *, output=VERILATOR_END, code=0, action="") -> Path:
    tool = tmp_path / "arbitrary_executable"
    tool.write_text(
        f"#!{sys.executable}\nimport os,sys,time,signal\n"
        "if '--version' in sys.argv: print('Fake Verilator 1'); raise SystemExit(0)\n"
        "if '-o' in sys.argv:\n"
        " from pathlib import Path\n"
        " p=Path(sys.argv[sys.argv.index('-o')+1]);p.write_text('fake build product')\n"
        f"print({output!r},end='',flush=True)\n{action}\nraise SystemExit({code})\n",
        encoding="utf-8",
    )
    tool.chmod(0o755)
    return tool


def _native(tmp_path: Path, tool: Path, backend="verilator") -> tuple[list[str], Path]:
    package = tmp_path / "package"
    package.mkdir()
    (package / "top.sv").write_text("module top(); endmodule\n")
    filelist = package / "complete.f"
    filelist.write_text("top.sv\n")
    report = tmp_path / "receipt.json"
    return ["compile", "--backend", backend, "--tool", str(tool), "--filelist", str(filelist),
            "--top", "top", "--cwd", str(package), "--work-dir", str(tmp_path / "work"),
            "--report", str(report)], report


def _manifest(tmp_path: Path) -> Path:
    output = tmp_path / "generated"
    output.mkdir()
    records = []
    for kind in ("register_rtl", "c_header", "verilog_header", "ralf", "json", "filelist"):
        path = output / ("top.v" if kind == "register_rtl" else kind)
        text = "module top(); endmodule\n" if kind == "register_rtl" else "output\n"
        if kind == "filelist":
            text = str(output / "top.v") + "\n"
        path.write_text(text)
        records.append({"class": kind, "status": "generated", "path": str(path.relative_to(tmp_path)),
                        "size_bytes": path.stat().st_size, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()})
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"schema_version": 1, "model": {"id": "unit", "path": "model.json", "sha256": "0" * 64},
                                    "runtime": {}, "output_root": "generated", "artifacts": records[:-1],
                                    "auxiliary_artifacts": records[-1:], "verification_records": []}))
    return manifest


def test_explicit_manifest_is_read_only_and_does_not_qualify(tmp_path, capsys):
    manifest = _manifest(tmp_path)
    before = {p: p.read_bytes() for p in tmp_path.rglob("*") if p.is_file()}
    tool = _fake(tmp_path, output="%Warning-UNUSEDSIGNAL: top.v:1: Signal is not used: 'notification'\n" + VERILATOR_END)
    report = tmp_path / "receipt.json"
    assert main(["compile", "--backend", "verilator", "--manifest", str(manifest), "--tool", str(tool),
                 "--work-dir", str(tmp_path / "work"), "--report", str(report)]) == 0
    result = json.loads(report.read_text())
    assert result["command"][1:5] == ["--lint-only", "-Wall", "-Wno-fatal", "--top-module"]
    assert result["top"] == "top"
    assert result["exit_code"] == 0 and result["candidate_acceptance"] == "NOT_EVALUATED"
    assert result["coverage"]["operation"] == ["parse", "elaboration", "enabled_lint"]
    assert result["coverage"]["behavior"] == result["coverage"]["required_project_structure"] == "NOT_EVALUATED"
    assert result["diagnostics"][0]["code"] == "UNUSEDSIGNAL"
    assert "notification" in result["diagnostics"][0]["raw"]
    assert {p: p.read_bytes() for p in before} == before
    assert json.loads(capsys.readouterr().out)["mode"] == "parse_elaboration_lint"


def test_vcs_recipe_is_selected_independently_of_executable_name(tmp_path):
    tool = _fake(tmp_path, output="Version W-test\nLint-[ONGS] Output never gets set\nfile.sv, 3\nobject: required_output\n" + VCS_END)
    argv, report = _native(tmp_path, tool, "vcs")
    assert main(argv) == 0  # Operation only; ONGS remains for the project consumer.
    result = json.loads(report.read_text())
    assert result["command"][1:5] == ["-full64", "-sverilog", "+lint=all", "-notice"]
    assert "--lint-only" not in result["command"]
    assert result["version"] == "Version W-test"
    assert "required_output" in result["diagnostics"][0]["raw"]
    assert result["candidate_acceptance"] == "NOT_EVALUATED"
    assert "link" in result["coverage"]["operation"]
    assert result["coverage"]["cross_backend_diagnostic_equivalence"] is False


@pytest.mark.parametrize("output,raw_code,cli_code,status", [
    ("%Error: syntax error\n", 17, 1, "FAIL"),
    ("%Error: real error despite process zero\n", 0, 1, "FAIL"),
    ("", 0, 2, "NOT_EVALUATED"),
    ("unrecognized success output\n", 0, 2, "NOT_EVALUATED"),
    ("Warning: unknown diagnostic format\n" + VERILATOR_END, 0, 2, "NOT_EVALUATED"),
    ("- Verilator: Built from truncated report\n", 0, 2, "NOT_EVALUATED"),
])
def test_raw_exit_and_cli_classification_are_separate(tmp_path, output, raw_code, cli_code, status):
    argv, report = _native(tmp_path, _fake(tmp_path, output=output, code=raw_code))
    assert main(argv) == cli_code
    result = json.loads(report.read_text())
    assert result["exit_code"] == raw_code
    assert result["cli_exit_code"] == cli_code
    assert result["compilation_status"] == status
    assert Path(result["log_path"]).read_text() == output


@pytest.mark.parametrize("action,timeout,expected_signal,timed_out", [
    ("os.kill(os.getpid(),signal.SIGTERM)", 5, signal.SIGTERM, False),
    ("time.sleep(5)", .05, signal.SIGKILL, True),
])
def test_signal_and_timeout_are_actual_process_facts(tmp_path, action, timeout, expected_signal, timed_out):
    argv, report = _native(tmp_path, _fake(tmp_path, action=action))
    assert main([*argv, "--timeout", str(timeout)]) == 1
    result = json.loads(report.read_text())
    assert result["exit_code"] == -expected_signal
    assert result["timed_out"] is timed_out


def test_previous_attempt_is_not_overwritten(tmp_path):
    argv, report = _native(tmp_path, _fake(tmp_path, output="%Error: intentional\n", code=9))
    assert main(argv) == 1
    before = report.read_bytes()
    with pytest.raises(RuntimeConfigurationError, match="fresh"):
        main(argv)
    assert report.read_bytes() == before


def test_unsupported_filelist_is_not_silently_dropped(tmp_path):
    argv, report = _native(tmp_path, _fake(tmp_path))
    (tmp_path / "package/complete.f").write_text("--bbox-unsup\ntop.sv\n")
    assert main(argv) == 2
    result = json.loads(report.read_text())
    assert result["exit_code"] is None and result["command"] == []
    assert result["compilation_status"] == "NOT_EVALUATED"


def test_legacy_compile_still_writes_only_v1_strict_record(tmp_path):
    manifest = _manifest(tmp_path)
    tool = _fake(tmp_path, output="strict-control\n")
    assert main(["compile", "--manifest", str(manifest), "--tool", str(tool)]) == 0
    stored = json.loads(manifest.read_text())
    assert stored["schema_version"] == 1
    assert len(stored["verification_records"]) == 1
    record = stored["verification_records"][0]
    assert record["kind"] == "strict_compile"
    assert record["argv"][1:4] == ["--lint-only", "-Wall", "-f"]
    assert "-Wno-fatal" not in record["argv"]


def test_backend_is_required_for_new_options(tmp_path):
    manifest = _manifest(tmp_path)
    with pytest.raises(SystemExit) as error:
        main(["compile", "--manifest", str(manifest), "--tool", "verilator", "--work-dir", str(tmp_path / "work")])
    assert error.value.code == 2


@pytest.mark.parametrize("timeout,expected_exit", [(None, 0), ("300", 2), ("299", 2)])
def test_legacy_timeout_option_presence_is_not_its_numeric_default(tmp_path, monkeypatch, timeout, expected_exit):
    calls = []

    def legacy(manifest, tool):
        calls.append((manifest, tool))
        return {"exit_code": 0}

    monkeypatch.setattr(selftest, "compile_rtl", legacy)
    manifest = tmp_path / "not_opened.json"
    argv = ["compile", "--manifest", str(manifest), "--tool", "legacy_tool"]
    if timeout is not None:
        argv.extend(["--timeout", timeout])
    if expected_exit:
        with pytest.raises(SystemExit) as error:
            main(argv)
        assert error.value.code == expected_exit
        assert calls == []
    else:
        assert main(argv) == 0
        assert calls == [(manifest, "legacy_tool")]


@pytest.mark.parametrize("timeout,expected_timeout", [(None, 300.0), ("300", 300.0), ("299", 299.0)])
def test_backend_timeout_applies_default_only_when_omitted(tmp_path, monkeypatch, timeout, expected_timeout):
    calls = []

    def backend(args):
        calls.append(args.timeout)
        return {"cli_exit_code": 0}

    monkeypatch.setattr(selftest, "_compile_backend", backend)
    argv = ["compile", "--backend", "verilator", "--filelist", str(tmp_path / "not_opened.f")]
    if timeout is not None:
        argv.extend(["--timeout", timeout])
    assert main(argv) == 0
    assert calls == [expected_timeout]
