#!/usr/bin/env python3
"""Vendor or verify the Viewer template built by the pinned apv_html source."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import tempfile
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
VIEWER_PATH = Path("viewer/apv_html")
DEFAULT_SOURCE = (
    PROJECT_ROOT / VIEWER_PATH / "dist/address-planner-viewer.template.html"
)
DEFAULT_TARGET = (
    PROJECT_ROOT
    / "address_planner/report_template/address_planner_viewer.template.html"
)
DEFAULT_LOCK = PROJECT_ROOT / "viewer-template.lock.json"
VIEWER_REPOSITORY = "https://github.com/fliibs/apv_html.git"
LOCK_VERSION = 1
CONTAINER_VERSIONS = (1,)
SQLITE_SCHEMA_VERSIONS = (1,)
PLACEHOLDERS = (
    "__APV_MANIFEST__",
    "__APV_DATABASE_GZIP_BASE64__",
)


def _relative(path: Path) -> str:
    return path.resolve().relative_to(PROJECT_ROOT).as_posix()


def _sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _validate_template(payload: bytes, label: str) -> None:
    try:
        text = payload.decode("utf-8")
    except UnicodeDecodeError as error:
        raise SystemExit(f"{label}: Viewer template must be UTF-8") from error
    for placeholder in PLACEHOLDERS:
        count = text.count(placeholder)
        if count != 1:
            raise SystemExit(f"{label}: {placeholder}: expected once, found {count}")
    if b"<script" not in payload or b'apv-sqlite-wasm' not in payload:
        raise SystemExit(f"{label}: embedded SQLite runtime is missing")
    if b'apv-worker-runtime' not in payload:
        raise SystemExit(f"{label}: embedded Worker runtime is missing")


def _git(*args: str, cwd: Path = PROJECT_ROOT) -> str:
    try:
        result = subprocess.run(
            ("git", *args),
            cwd=cwd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    except subprocess.CalledProcessError as error:
        detail = error.stderr.strip() or error.stdout.strip() or str(error)
        raise SystemExit(f"git {' '.join(args)} failed: {detail}") from error
    return result.stdout.strip()


def _viewer_commit() -> str:
    viewer_root = PROJECT_ROOT / VIEWER_PATH
    if not viewer_root.is_dir():
        raise SystemExit(
            f"Viewer submodule is missing: {viewer_root}; run "
            "git submodule update --init --recursive"
        )
    return _git("rev-parse", "HEAD", cwd=viewer_root)


def _viewer_repository() -> str:
    repository = _git(
        "config",
        "-f",
        ".gitmodules",
        "--get",
        f"submodule.{VIEWER_PATH.as_posix()}.url",
    )
    if repository != VIEWER_REPOSITORY:
        raise SystemExit(
            "Viewer submodule repository does not match the provenance contract: "
            f"{repository!r} != {VIEWER_REPOSITORY!r}"
        )
    return repository


def _gitlink_commit() -> str:
    row = _git("ls-files", "--stage", "--", VIEWER_PATH.as_posix())
    if not row:
        raise SystemExit(f"Viewer gitlink is not tracked: {VIEWER_PATH}")
    metadata = row.split("\t", 1)[0].split()
    if len(metadata) != 3 or metadata[0] != "160000":
        raise SystemExit(f"Viewer path is not a submodule gitlink: {row!r}")
    return metadata[1]


def _lock_payload(template: bytes, viewer_commit: str) -> dict:
    return {
        "lock_version": LOCK_VERSION,
        "viewer": {
            "repository": _viewer_repository(),
            "path": VIEWER_PATH.as_posix(),
            "commit": viewer_commit,
        },
        "template": {
            "source": _relative(DEFAULT_SOURCE),
            "vendored": _relative(DEFAULT_TARGET),
            "size_bytes": len(template),
            "sha256": _sha256(template),
        },
        "compatibility": {
            "container_versions": list(CONTAINER_VERSIONS),
            "sqlite_schema_versions": list(SQLITE_SCHEMA_VERSIONS),
        },
    }


def _atomic_write(path: Path, payload: bytes, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = tempfile.NamedTemporaryFile(
        prefix=f".{path.name}.", suffix=".tmp", dir=path.parent, delete=False
    )
    temporary_path = Path(temporary.name)
    try:
        with temporary:
            temporary.write(payload)
            temporary.flush()
            os.fsync(temporary.fileno())
        os.chmod(temporary_path, mode)
        os.replace(temporary_path, path)
    except BaseException:
        temporary_path.unlink(missing_ok=True)
        raise


def _publication_mode(target: Path, source: Path) -> int:
    try:
        return stat.S_IMODE(target.stat().st_mode)
    except FileNotFoundError:
        return stat.S_IMODE(source.stat().st_mode) & 0o666 or 0o644


def _check(source: Path, target: Path, lock_path: Path) -> None:
    if not source.is_file():
        raise SystemExit(f"Viewer build is missing: {source}; run npm run build")
    if not target.is_file():
        raise SystemExit(f"Vendored Viewer template is missing: {target}")
    if not lock_path.is_file():
        raise SystemExit(f"Viewer template lock is missing: {lock_path}")

    source_payload = source.read_bytes()
    target_payload = target.read_bytes()
    _validate_template(source_payload, str(source))
    _validate_template(target_payload, str(target))
    if source_payload != target_payload:
        raise SystemExit(
            "Viewer build differs from the vendored template; run "
            "python tools/sync_viewer_template.py"
        )

    try:
        lock = json.loads(lock_path.read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as error:
        raise SystemExit(f"Viewer template lock is invalid: {lock_path}") from error

    expected = _lock_payload(target_payload, _viewer_commit())
    if lock != expected:
        raise SystemExit(
            "Viewer template lock does not match the submodule or artifact; run "
            "python tools/sync_viewer_template.py"
        )
    gitlink_commit = _gitlink_commit()
    if gitlink_commit != expected["viewer"]["commit"]:
        raise SystemExit(
            "Viewer submodule HEAD does not match the superproject gitlink: "
            f"{expected['viewer']['commit']} != {gitlink_commit}"
        )
    print(
        "verified Viewer template: "
        f"{target} ({len(target_payload)} bytes, sha256={_sha256(target_payload)})"
    )


def _sync(source: Path, target: Path, lock_path: Path) -> None:
    if source.resolve() != DEFAULT_SOURCE.resolve():
        raise SystemExit(
            f"the pinned Viewer build must come from {DEFAULT_SOURCE}; got {source}"
        )
    if target.resolve() != DEFAULT_TARGET.resolve():
        raise SystemExit(
            f"the vendored Viewer target must be {DEFAULT_TARGET}; got {target}"
        )
    payload = source.read_bytes() if source.is_file() else None
    if payload is None:
        raise SystemExit(f"Viewer build does not exist: {source}; run npm run build")
    _validate_template(payload, str(source))

    _atomic_write(target, payload, _publication_mode(target, source))
    lock = _lock_payload(payload, _viewer_commit())
    lock_bytes = (json.dumps(lock, indent=2, sort_keys=True) + "\n").encode("utf-8")
    _atomic_write(lock_path, lock_bytes, 0o644)

    print(
        f"vendored Viewer template: {target} "
        f"({len(payload)} bytes, sha256={_sha256(payload)})"
    )
    print(f"updated Viewer template lock: {lock_path}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="vendor or verify the pinned apv_html Viewer template"
    )
    parser.add_argument(
        "template",
        nargs="?",
        type=Path,
        default=DEFAULT_SOURCE,
        help="apv_html template build (defaults to the pinned submodule build)",
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_TARGET)
    parser.add_argument("--lock", type=Path, default=DEFAULT_LOCK)
    parser.add_argument(
        "--check",
        action="store_true",
        help="verify the submodule, lock and vendored template without writing",
    )
    args = parser.parse_args()

    source = args.template.expanduser().resolve()
    target = args.output.expanduser().resolve()
    lock_path = args.lock.expanduser().resolve()
    if args.check:
        _check(source, target, lock_path)
    else:
        _sync(source, target, lock_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
