#!/usr/bin/env python3
"""Snapshot and verify that a formal skill package was not mutated by tests."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import tempfile
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
_CACHE_DIRECTORIES = frozenset(
    {
        "__pycache__",
        ".pytest_cache",
        ".hypothesis",
        ".mypy_cache",
        ".ruff_cache",
        ".tox",
        ".nox",
    }
)


class GuardError(RuntimeError):
    """Raised for an unsafe target or malformed inventory."""


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _value_sha256(value: Any) -> str:
    encoded = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _is_cache_path(relative: str) -> bool:
    path = Path(relative)
    if any(part in _CACHE_DIRECTORIES for part in path.parts):
        return True
    name = path.name
    return (
        name.endswith((".pyc", ".pyo"))
        or name == ".coverage"
        or name.startswith(".coverage.")
    )


def _validated_root(root: Path) -> Path:
    expanded = root.expanduser()
    if expanded.is_symlink():
        raise GuardError(f"formal skill root must not be a symlink: {expanded}")
    resolved = expanded.resolve()
    if not resolved.is_dir() or resolved == Path("/"):
        raise GuardError(f"formal skill root must be a real, non-root directory: {resolved}")
    return resolved


def _validated_report(root: Path, report: Path) -> Path:
    resolved = report.expanduser().resolve()
    if resolved == root or root in resolved.parents:
        raise GuardError(f"inventory report must be outside the formal skill package: {resolved}")
    if resolved.exists() and (resolved.is_symlink() or not resolved.is_file()):
        raise GuardError(f"inventory report must be a regular file when present: {resolved}")
    resolved.parent.mkdir(parents=True, exist_ok=True)
    return resolved


def _entry(path: Path, root: Path) -> dict[str, Any]:
    relative = path.relative_to(root).as_posix()
    metadata = path.lstat()
    common: dict[str, Any] = {
        "path": relative,
        "mode": stat.S_IMODE(metadata.st_mode),
        "cache_path": _is_cache_path(relative),
    }
    if path.is_symlink():
        return {**common, "kind": "symlink", "target": os.readlink(path)}
    if path.is_dir():
        return {**common, "kind": "directory"}
    if path.is_file():
        return {
            **common,
            "kind": "file",
            "size_bytes": metadata.st_size,
            "sha256": _sha256(path),
        }
    raise GuardError(f"unsupported filesystem entry in formal skill package: {path}")


def inventory(root: Path) -> dict[str, Any]:
    """Return a deterministic content and cache inventory without mutating ``root``."""

    resolved = _validated_root(root)
    entries: list[dict[str, Any]] = []
    pending = [resolved]
    while pending:
        directory = pending.pop()
        for child in sorted(directory.iterdir(), key=lambda item: item.name, reverse=True):
            item = _entry(child, resolved)
            entries.append(item)
            if item["kind"] == "directory":
                pending.append(child)
    entries.sort(key=lambda item: item["path"])
    cache_entries = [entry for entry in entries if entry["cache_path"]]
    return {
        "schema_version": SCHEMA_VERSION,
        "root": str(resolved),
        "entry_count": len(entries),
        "file_count": sum(entry["kind"] == "file" for entry in entries),
        "package_digest": _value_sha256(entries),
        "cache_digest": _value_sha256(cache_entries),
        "cache_paths": [entry["path"] for entry in cache_entries],
        "entries": entries,
    }


def _write_json(path: Path, payload: dict[str, Any]) -> None:
    temporary: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as stream:
            temporary = Path(stream.name)
            json.dump(payload, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None and temporary.exists():
            temporary.unlink()


def snapshot(root: Path, report: Path) -> dict[str, Any]:
    resolved_root = _validated_root(root)
    resolved_report = _validated_report(resolved_root, report)
    payload = inventory(resolved_root)
    _write_json(resolved_report, payload)
    return payload


def verify(root: Path, before_report: Path, report: Path) -> dict[str, Any]:
    resolved_root = _validated_root(root)
    resolved_report = _validated_report(resolved_root, report)
    before_path = before_report.expanduser().resolve()
    if before_path == resolved_report:
        raise GuardError("before and verification reports must use distinct paths")
    try:
        before = json.loads(before_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise GuardError(f"cannot read formal skill pre-inventory {before_path}: {error}") from error
    if before.get("schema_version") != SCHEMA_VERSION or before.get("root") != str(resolved_root):
        raise GuardError("formal skill pre-inventory schema/root does not match the requested package")
    if not isinstance(before.get("entries"), list):
        raise GuardError("formal skill pre-inventory has no entry list")

    after = inventory(resolved_root)
    before_entries = {entry["path"]: entry for entry in before["entries"]}
    after_entries = {entry["path"]: entry for entry in after["entries"]}
    added = sorted(set(after_entries) - set(before_entries))
    removed = sorted(set(before_entries) - set(after_entries))
    modified = sorted(
        path for path in set(before_entries) & set(after_entries)
        if before_entries[path] != after_entries[path]
    )
    cache_mutations = sorted(
        path for path in set(added + removed + modified) if _is_cache_path(path)
    )
    unchanged = not added and not removed and not modified
    payload = {
        "schema_version": SCHEMA_VERSION,
        "result": "pass" if unchanged else "fail",
        "root": str(resolved_root),
        "before_report": str(before_path),
        "before_report_sha256": _sha256(before_path),
        "before_package_digest": before["package_digest"],
        "after_package_digest": after["package_digest"],
        "before_cache_digest": before["cache_digest"],
        "after_cache_digest": after["cache_digest"],
        "preexisting_cache_paths": before["cache_paths"],
        "after_cache_paths": after["cache_paths"],
        "preexisting_cache_unchanged": before["cache_digest"] == after["cache_digest"],
        "formal_package_unchanged": unchanged,
        "added_paths": added,
        "removed_paths": removed,
        "modified_paths": modified,
        "cache_mutations": cache_mutations,
        "after_inventory": after,
    }
    _write_json(resolved_report, payload)
    return payload


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="snapshot or verify that tests did not mutate a formal skill package"
    )
    subcommands = parser.add_subparsers(dest="command", required=True)
    snapshot_parser = subcommands.add_parser("snapshot")
    snapshot_parser.add_argument("--root", required=True, type=Path)
    snapshot_parser.add_argument("--report", required=True, type=Path)
    verify_parser = subcommands.add_parser("verify")
    verify_parser.add_argument("--root", required=True, type=Path)
    verify_parser.add_argument("--before", required=True, type=Path)
    verify_parser.add_argument("--report", required=True, type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    arguments = _parser().parse_args(argv)
    try:
        if arguments.command == "snapshot":
            payload = snapshot(arguments.root, arguments.report)
            summary = {
                "result": "snapshot",
                "report": str(arguments.report.resolve()),
                "entry_count": payload["entry_count"],
                "package_digest": payload["package_digest"],
                "cache_digest": payload["cache_digest"],
                "preexisting_cache_paths": payload["cache_paths"],
            }
            print(json.dumps(summary, sort_keys=True))
            return 0
        payload = verify(arguments.root, arguments.before, arguments.report)
        print(
            json.dumps(
                {
                    "result": payload["result"],
                    "report": str(arguments.report.resolve()),
                    "formal_package_unchanged": payload["formal_package_unchanged"],
                    "cache_mutations": payload["cache_mutations"],
                    "package_digest": payload["after_package_digest"],
                },
                sort_keys=True,
            )
        )
        return 0 if payload["result"] == "pass" else 1
    except GuardError as error:
        print(json.dumps({"result": "error", "error": str(error)}, sort_keys=True))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
