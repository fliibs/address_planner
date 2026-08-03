"""Package a validated SQLite report into the offline APV single-HTML viewer."""

from __future__ import annotations

import base64
import gzip
import hashlib
import json
import os
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .sqlite_report import SQLiteReportInfo, validate_sqlite_report


CONTAINER_VERSION = 1
MANIFEST_PLACEHOLDER = "__APV_MANIFEST__"
DATABASE_PLACEHOLDER = "__APV_DATABASE_GZIP_BASE64__"
DEFAULT_VIEWER_TEMPLATE_NAME = "address_planner_viewer.template.html"


@dataclass(frozen=True)
class SingleHTMLReportInfo:
    """Verified measurements for one packaged, offline viewer report."""

    path: Path
    html_bytes: int
    html_sha256: str
    database_bytes: int
    compressed_database_bytes: int
    database_sha256: str
    root_count: int
    node_count: int
    field_count: int
    manifest: Mapping[str, object]


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _publication_mode(target: Path) -> int:
    try:
        return stat.S_IMODE(target.stat().st_mode)
    except FileNotFoundError:
        return 0o644


def _safe_manifest_json(manifest: Mapping[str, object]) -> str:
    """Serialize JSON safely for a ``<script type=application/json>`` body."""

    # ensure_ascii also escapes U+2028/U+2029. Escaping '<' prevents a value
    # containing '</script>' from terminating the raw-text element early.
    return json.dumps(
        manifest,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).replace("<", "\\u003c")


def _validate_template(template: str, template_path: Path) -> None:
    for placeholder in (MANIFEST_PLACEHOLDER, DATABASE_PLACEHOLDER):
        count = template.count(placeholder)
        if count != 1:
            raise ValueError(
                f"viewer template {template_path} must contain {placeholder!r} "
                f"exactly once; found {count}"
            )


def default_viewer_template_path() -> Path:
    """Return the Viewer template vendored with the Python package."""

    template = (
        Path(__file__).resolve().parent
        / "report_template"
        / DEFAULT_VIEWER_TEMPLATE_NAME
    )
    if not template.is_file():
        raise FileNotFoundError(
            "the bundled single-HTML Viewer template is missing; rebuild apv_html "
            "and run tools/sync_viewer_template.py"
        )
    return template


def package_single_html(
    database_path,
    viewer_template_path,
    output_html_path,
    *,
    compression_level: int = 9,
) -> SingleHTMLReportInfo:
    """Atomically embed a validated SQLite report in a self-contained HTML.

    The viewer template owns JavaScript, CSS, SQLite WASM and Worker code. It
    exposes exactly two placeholders: a JSON manifest and a standard-Base64
    gzip payload. The database remains a separate input so this function can
    validate and measure it before publication.
    """

    if not isinstance(compression_level, int) or isinstance(compression_level, bool):
        raise TypeError("compression_level must be an integer")
    if not 0 <= compression_level <= 9:
        raise ValueError("compression_level must be between 0 and 9")

    database_info: SQLiteReportInfo = validate_sqlite_report(database_path)
    database_bytes = database_info.path.read_bytes()
    if len(database_bytes) != database_info.database_bytes:
        raise ValueError("SQLite report changed while it was being packaged")
    database_sha256 = _sha256_bytes(database_bytes)
    if database_sha256 != database_info.sha256:
        raise ValueError("SQLite report hash changed while it was being packaged")

    compressed = gzip.compress(
        database_bytes,
        compresslevel=compression_level,
        mtime=0,
    )
    manifest = {
        "containerVersion": CONTAINER_VERSION,
        "schemaVersion": int(database_info.metadata["schema_version"]),
        "codec": "gzip+base64",
        "databaseSha256": database_sha256,
        "databaseBytes": len(database_bytes),
        "compressedBytes": len(compressed),
    }

    template_path = Path(viewer_template_path).expanduser().resolve()
    if not template_path.is_file():
        raise FileNotFoundError(f"viewer template does not exist: {template_path}")
    template = template_path.read_text(encoding="utf-8")
    _validate_template(template, template_path)

    html_text = template.replace(
        MANIFEST_PLACEHOLDER, _safe_manifest_json(manifest)
    ).replace(
        DATABASE_PLACEHOLDER, base64.b64encode(compressed).decode("ascii")
    )
    if MANIFEST_PLACEHOLDER in html_text or DATABASE_PLACEHOLDER in html_text:
        raise ValueError("viewer template placeholders remain after packaging")
    html_bytes = html_text.encode("utf-8")

    target = Path(output_html_path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary_file = tempfile.NamedTemporaryFile(
        prefix=f".{target.name}.",
        suffix=".tmp",
        dir=str(target.parent),
        delete=False,
    )
    temporary_path = Path(temporary_file.name)
    try:
        with temporary_file:
            temporary_file.write(html_bytes)
            temporary_file.flush()
            os.fsync(temporary_file.fileno())
        os.chmod(temporary_path, _publication_mode(target))
        os.replace(temporary_path, target)
    except BaseException:
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass
        raise

    return SingleHTMLReportInfo(
        path=target,
        html_bytes=len(html_bytes),
        html_sha256=_sha256_bytes(html_bytes),
        database_bytes=len(database_bytes),
        compressed_database_bytes=len(compressed),
        database_sha256=database_sha256,
        root_count=database_info.root_count,
        node_count=database_info.node_count,
        field_count=database_info.field_count,
        manifest=manifest,
    )


__all__ = [
    "CONTAINER_VERSION",
    "DATABASE_PLACEHOLDER",
    "DEFAULT_VIEWER_TEMPLATE_NAME",
    "MANIFEST_PLACEHOLDER",
    "SingleHTMLReportInfo",
    "default_viewer_template_path",
    "package_single_html",
]
