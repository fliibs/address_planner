"""Focused transaction and target-safety tests for canonical JSON generation."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest

import address_planner.selftest as selftest
from address_planner.selftest import RuntimeConfigurationError, generate, inventory


def _model() -> dict:
    return {
        "schema_version": 1,
        "model_id": "atomic_model",
        "name": "atomic_bank",
        "description": "transactional generation test",
        "size_bytes": 64,
        "bus_width": 32,
        "software_interface": "apb",
        "registers": [
            {
                "name": "control",
                "offset_bytes": 0,
                "width_bits": 32,
                "fields": [
                    {
                        "name": "enable",
                        "lsb": 0,
                        "width_bits": 1,
                        "sw_access": "RW",
                        "hw_access": "RO",
                        "reset": 0,
                    }
                ],
            }
        ],
    }


def _tree_digest(root: Path) -> str:
    digest = hashlib.sha256()
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix().encode("utf-8")
        if path.is_symlink():
            digest.update(b"L\0" + relative + b"\0" + os.readlink(path).encode("utf-8"))
        elif path.is_dir():
            digest.update(b"D\0" + relative + b"\0")
        else:
            digest.update(b"F\0" + relative + b"\0" + hashlib.sha256(path.read_bytes()).digest())
    return digest.hexdigest()


def _stage_siblings(output_root: Path) -> list[Path]:
    return sorted(output_root.parent.glob(f".{output_root.name}.stage-*"))


def _baseline(tmp_path: Path) -> tuple[Path, Path, Path]:
    delivery = tmp_path / "delivery"
    delivery.mkdir()
    model_path = tmp_path / "model.json"
    output_root = delivery / "generated"
    manifest = delivery / "delivery_manifest.json"
    model_path.write_text(json.dumps(_model()), encoding="utf-8")
    generate(model_path, output_root, manifest)
    inventory(manifest)
    assert _stage_siblings(output_root) == []
    return model_path, output_root, manifest


@pytest.mark.parametrize("failure_point", ["backend", "stage_validation", "output_rename", "manifest_rename"])
def test_failed_generation_preserves_prior_delivery_at_every_publish_boundary(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, failure_point: str
) -> None:
    model_path, output_root, manifest = _baseline(tmp_path)
    old_tree_digest = _tree_digest(output_root)
    old_manifest = manifest.read_bytes()

    if failure_point == "backend":
        real_parse = selftest._parse_model

        def fail_backend(path: Path):
            model, _bank = real_parse(path)

            class BrokenBank:
                def generate(self, _path: str) -> None:
                    raise RuntimeError("injected backend failure")

            return model, BrokenBank()

        monkeypatch.setattr(selftest, "_parse_model", fail_backend)
    elif failure_point == "stage_validation":
        real_inventory = selftest.inventory

        def fail_staged_inventory(path: Path) -> dict:
            if Path(path).parent != manifest.parent:
                raise RuntimeConfigurationError("injected staged inventory failure")
            return real_inventory(path)

        monkeypatch.setattr(selftest, "inventory", fail_staged_inventory)
    else:
        real_replace = selftest._publish_replace
        failed = False
        target = output_root if failure_point == "output_rename" else manifest

        def fail_once(source: Path, destination: Path) -> None:
            nonlocal failed
            if destination == target and not failed:
                failed = True
                raise OSError(f"injected {failure_point} failure")
            real_replace(source, destination)

        monkeypatch.setattr(selftest, "_publish_replace", fail_once)

    with pytest.raises((OSError, RuntimeError, RuntimeConfigurationError), match="injected"):
        generate(model_path, output_root, manifest)

    assert _tree_digest(output_root) == old_tree_digest
    assert manifest.read_bytes() == old_manifest
    assert inventory(manifest)["artifact_count"] == 5
    assert _stage_siblings(output_root)


def test_failed_first_generation_publishes_neither_final_tree_nor_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    delivery = tmp_path / "delivery"
    delivery.mkdir()
    model_path = tmp_path / "model.json"
    output_root = delivery / "generated"
    manifest = delivery / "delivery_manifest.json"
    model_path.write_text(json.dumps(_model()), encoding="utf-8")
    real_parse = selftest._parse_model

    def fail_backend(path: Path):
        model, _bank = real_parse(path)

        class BrokenBank:
            def generate(self, _path: str) -> None:
                raise RuntimeError("injected first-publish backend failure")

        return model, BrokenBank()

    monkeypatch.setattr(selftest, "_parse_model", fail_backend)
    with pytest.raises(RuntimeError, match="injected first-publish"):
        generate(model_path, output_root, manifest)

    assert not output_root.exists()
    assert not manifest.exists()
    assert _stage_siblings(output_root)


def test_generate_rejects_unsafe_targets_without_final_publication(tmp_path: Path) -> None:
    model_path = tmp_path / "model.json"
    model_path.write_text(json.dumps(_model()), encoding="utf-8")
    delivery = tmp_path / "delivery"
    delivery.mkdir()
    outside = tmp_path / "outside"
    outside.mkdir()
    real_parent = tmp_path / "real_parent"
    real_parent.mkdir()
    linked_parent = tmp_path / "linked_parent"
    os.symlink(real_parent, linked_parent)

    unsafe = [
        (Path(delivery.anchor), delivery / "root_manifest.json", False),
        (delivery, delivery / "manifest.json", False),
        (outside / "generated", delivery / "manifest.json", True),
        (delivery / "generated", delivery / "generated" / "manifest.json", True),
        (linked_parent / "generated", linked_parent / "manifest.json", True),
    ]
    for output_root, manifest, output_must_be_absent in unsafe:
        with pytest.raises(RuntimeConfigurationError):
            generate(model_path, output_root, manifest)
        assert not manifest.exists()
        if output_must_be_absent:
            assert not output_root.exists()


def test_successful_rerun_is_deterministic_and_manifest_paths_are_final(tmp_path: Path) -> None:
    model_path, output_root, manifest = _baseline(tmp_path)
    first_tree_digest = _tree_digest(output_root)
    first_delivery_digest = _tree_digest(output_root.parent)
    first_manifest = manifest.read_bytes()

    generate(model_path, output_root, manifest)

    assert _tree_digest(output_root) == first_tree_digest
    assert _tree_digest(output_root.parent) == first_delivery_digest
    assert manifest.read_bytes() == first_manifest
    assert _stage_siblings(output_root) == []
    checked = inventory(manifest)
    assert checked["artifact_count"] == 5
    stored = json.loads(manifest.read_text(encoding="utf-8"))
    assert stored["output_root"] == "generated/atomic_bank"
    assert all(".stage-" not in record["path"] for record in stored["artifacts"])


def test_representative_primary_artifact_hashes_remain_established(tmp_path: Path) -> None:
    model_path = Path(os.environ["ADDRESS_PLANNER_MODEL_DEFINITION"])
    output_root = tmp_path / "generated"
    manifest = tmp_path / "delivery_manifest.json"
    generate(model_path, output_root, manifest)

    stored = json.loads(manifest.read_text(encoding="utf-8"))
    hashes = {record["class"]: record["sha256"] for record in stored["artifacts"]}
    assert hashes == {
        "register_rtl": "5b04cd54dcac9105b8bd6f80a308289be63010bdaaa4631c02ae67d9e1eabcb9",
        "c_header": "2d5937c6878790756d6dcb3b11108c5b20793eb4303e0b29db39eb4665628a2b",
        "verilog_header": "004186b97024f72cb7885acae72ed08144c7cb353db9ab3ad9fd2b3f23ece852",
        "ralf": "23c90687e5376ae7c1889175af9dfa8f24eebfb7f8bcbac105dfbb942ac7727f",
        "json": "48f7071d76209910c4831093556872c4d4c90498b52b54038efd88a7ac5fbbf7",
    }
    assert _stage_siblings(output_root) == []
