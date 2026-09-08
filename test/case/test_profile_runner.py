"""The profiling entry point preserves script arguments, cwd and exit status."""

import json
from pathlib import Path
import pstats
import subprocess
import sys

import pytest


@pytest.mark.parametrize("exit_code", [0, 7])
def test_profile_runner_preserves_script_contract(tmp_path, exit_code):
    project = Path(__file__).resolve().parents[2]
    source_dir = tmp_path / "scripts"
    source_dir.mkdir()
    (source_dir / "sibling.py").write_text("VALUE = 42\n")
    script = source_dir / "map.py"
    script.write_text(
        "import json, os, sys, sibling\n"
        "print(json.dumps([sys.argv, os.getcwd(), sibling.VALUE]))\n"
        + f"raise SystemExit({exit_code})\n"
    )
    profile = tmp_path / "map.pstats"
    result = subprocess.run(
        [sys.executable, str(project / "tools/profile_addrmap.py"),
         "--profile", str(profile), str(script), "--example", "hello world"],
        cwd=tmp_path, capture_output=True, text=True, timeout=30,
    )
    assert result.returncode == exit_code, result.stderr
    argv, cwd, value = json.loads(result.stdout)
    assert argv == [str(script), "--example", "hello world"]
    assert cwd == str(tmp_path) and value == 42
    assert pstats.Stats(str(profile)).total_calls > 0
    rows = [json.loads(line.split("] ", 1)[1])
            for line in result.stderr.splitlines()
            if line.startswith("[addr-planner-timing]")]
    end = next(row for row in rows if row["event"] == "end")
    assert end["phase"] == "script.total"
    assert end["status"] == ("error" if exit_code else "ok")
    assert any(row["event"] == "summary" for row in rows)
