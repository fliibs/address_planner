"""Regression tests for side-effect-free formal skill test execution."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from tools.formal_skill_guard import snapshot, verify


def _fake_skill(root: Path) -> None:
    root.mkdir()
    (root / "SKILL.md").write_text("---\nname: fake\ndescription: fake\n---\n", encoding="utf-8")
    (root / "test_fake.py").write_text("def test_true():\n    assert True\n", encoding="utf-8")
    bytecode = root / "__pycache__" / "historical.pyc"
    bytecode.parent.mkdir()
    bytecode.write_bytes(b"historical-bytecode")
    pytest_cache = root / ".pytest_cache"
    pytest_cache.mkdir()
    (pytest_cache / "CACHEDIR.TAG").write_text("historical-cache\n", encoding="utf-8")


def test_guard_preserves_and_reports_preexisting_cache_without_calling_it_clean(tmp_path: Path) -> None:
    skill = tmp_path / "formal_skill"
    _fake_skill(skill)
    before = tmp_path / "before.json"
    after = tmp_path / "after.json"
    initial = snapshot(skill, before)
    checked = verify(skill, before, after)

    assert checked["result"] == "pass"
    assert checked["formal_package_unchanged"] is True
    assert checked["preexisting_cache_unchanged"] is True
    assert checked["cache_mutations"] == []
    assert "__pycache__/historical.pyc" in initial["cache_paths"]
    assert ".pytest_cache/CACHEDIR.TAG" in checked["preexisting_cache_paths"]


def test_guard_rejects_new_or_modified_cache_and_records_exact_paths(tmp_path: Path) -> None:
    skill = tmp_path / "formal_skill"
    _fake_skill(skill)
    before = tmp_path / "before.json"
    snapshot(skill, before)

    historical = skill / "__pycache__" / "historical.pyc"
    historical.write_bytes(b"modified-bytecode")
    new_cache = skill / ".pytest_cache" / "new-entry"
    new_cache.write_text("new\n", encoding="utf-8")
    report = tmp_path / "after.json"
    checked = verify(skill, before, report)

    assert checked["result"] == "fail"
    assert checked["formal_package_unchanged"] is False
    assert checked["preexisting_cache_unchanged"] is False
    assert checked["modified_paths"] == ["__pycache__/historical.pyc"]
    assert checked["added_paths"] == [".pytest_cache/new-entry"]
    assert checked["cache_mutations"] == [
        ".pytest_cache/new-entry",
        "__pycache__/historical.pyc",
    ]


def test_real_pytest_execution_is_bytecode_and_cache_isolated(tmp_path: Path) -> None:
    skill = tmp_path / "formal_skill"
    _fake_skill(skill)
    before = tmp_path / "before.json"
    after = tmp_path / "after.json"
    snapshot(skill, before)

    environment = os.environ.copy()
    for name in ("PYTHONHOME", "PYTHONPATH", "PYTHONPYCACHEPREFIX", "PYTEST_ADDOPTS"):
        environment.pop(name, None)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    environment["PYTEST_DISABLE_PLUGIN_AUTOLOAD"] = "1"
    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "-q",
            "-p",
            "no:cacheprovider",
            "--basetemp",
            str(tmp_path / "pytest_tmp"),
            str(skill / "test_fake.py"),
        ],
        cwd=tmp_path,
        env=environment,
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert "1 passed" in completed.stdout

    checked = verify(skill, before, after)
    assert checked["result"] == "pass"
    assert checked["cache_mutations"] == []
    assert checked["preexisting_cache_paths"] == checked["after_cache_paths"]


def test_guard_cli_returns_nonzero_for_formal_package_mutation(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    script = root / "tools" / "formal_skill_guard.py"
    skill = tmp_path / "formal_skill"
    _fake_skill(skill)
    before = tmp_path / "before.json"
    after = tmp_path / "after.json"
    snapshot(skill, before)
    (skill / "test_fake.py").write_text("def test_true():\n    assert False\n", encoding="utf-8")

    completed = subprocess.run(
        [sys.executable, str(script), "verify", "--root", str(skill), "--before", str(before), "--report", str(after)],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 1
    summary = json.loads(completed.stdout)
    assert summary["result"] == "fail"
    assert json.loads(after.read_text(encoding="utf-8"))["modified_paths"] == ["test_fake.py"]


def test_formal_skill_runner_always_reports_real_pytest_and_unchanged_package(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[2]
    runner = root / "tools" / "run_formal_skill_tests.py"
    skill = tmp_path / "formal_skill"
    _fake_skill(skill)
    quick_validate = tmp_path / "quick_validate.py"
    quick_validate.write_text(
        "from pathlib import Path\nimport sys\nassert (Path(sys.argv[1]) / 'SKILL.md').is_file()\nprint('Skill is valid!')\n",
        encoding="utf-8",
    )
    work = tmp_path / "work"
    manifest = work / "manifest.json"
    junit = work / "skill_tests.xml"
    completed = subprocess.run(
        [
            sys.executable,
            "-B",
            str(runner),
            "--skill-root",
            str(skill),
            "--address-planner-root",
            str(root),
            "--uhdl-root",
            str(root.parent / "uhdl"),
            "--work-root",
            str(work),
            "--manifest",
            str(manifest),
            "--junit",
            str(junit),
            "--quick-validate",
            str(quick_validate),
            "--quick-validate-python",
            sys.executable,
            "--python",
            sys.executable,
            "--test",
            "test_fake.py",
        ],
        text=True,
        capture_output=True,
        check=False,
    )
    assert completed.returncode == 0, completed.stdout + completed.stderr
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    assert payload["result"] == "pass"
    assert payload["pytest"]["exit_code"] == 0
    assert payload["pytest"]["junit"]["counts"] == {
        "tests": 1,
        "failures": 0,
        "errors": 0,
        "skipped": 0,
    }
    assert payload["quick_validate"]["exit_code"] == 0
    assert payload["formal_skill_inventory"]["formal_package_unchanged"] is True
    assert payload["formal_skill_inventory"]["cache_mutations"] == []
