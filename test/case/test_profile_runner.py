"""The profiling entry point preserves script arguments, cwd and exit status."""

import json
import os
from pathlib import Path
import pstats
import subprocess
import sys

import pytest


@pytest.mark.parametrize("exit_code", [0, 7])
@pytest.mark.parametrize("level", [1, 2, 3])
def test_profile_runner_preserves_script_contract(tmp_path, exit_code, level):
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
         "--timing-level", str(level), "--profile", str(profile), str(script), "--example", "hello world"],
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
    if level == 1:
        assert result.stderr == ''
        return
    end = next(row for row in rows if row["event"] == "end")
    assert end["phase"] == "script.total"
    assert end["status"] == ("error" if exit_code else "ok")
    assert any(row["event"] == "summary" for row in rows)


@pytest.mark.parametrize('options, expected', [
    ([], 1), (['--timing-level', '1'], 1),
    (['--timing-level', '2'], 2), (['--timing-level', '3'], 3),
    (['--timing-detail', 'coarse'], 2), (['--timing-detail', 'detailed'], 3),
])
def test_timing_levels_preserve_application_output(tmp_path, options, expected):
    project = Path(__file__).resolve().parents[2]
    script = tmp_path / 'model.py'
    script.write_text(
        'import sys\nprint("before planner import", flush=True)\n'
        'print("original diagnostic", file=sys.stderr, flush=True)\n'
        'from address_planner.timing import phase\n'
        'with phase("add_ralf", "input.ralf", progress=True):\n'
        '    with phase("ralf.read", "input.ralf", progress=True):\n'
        '        print("original generation output")\n'
    )
    env = {**os.environ, 'ADDRESS_PLANNER_ROOT': str(project), 'PYTHONPATH': str(project),
           'ADDRESS_PLANNER_TIMING': '1', 'ADDRESS_PLANNER_TIMING_DETAIL': 'detailed'}
    env.pop('ADDRESS_PLANNER_TIMING_LEVEL', None)
    baseline = subprocess.run([sys.executable, str(script)], cwd=tmp_path,
        env={**env, 'ADDRESS_PLANNER_TIMING_LEVEL': '1'}, capture_output=True, text=True, check=True)
    actual = subprocess.run([sys.executable, str(project/'tools/profile_addrmap.py'),
        *options, str(script)], cwd=tmp_path, env=env, capture_output=True, text=True, check=True)
    assert actual.stdout == baseline.stdout
    if expected == 1:
        assert actual.stderr == baseline.stderr
    else:
        events = [json.loads(line.split('] ', 1)[1]) for line in actual.stderr.splitlines()
                  if line.startswith('[addr-planner-timing] ')]
        phases = {row['phase'] for row in events if row['event'] == 'summary'}
        assert phases == ({'script.total', 'add_ralf', 'ralf.read'} if expected == 3
                          else {'script.total', 'add_ralf'})
