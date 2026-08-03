#!/usr/bin/env python3
"""Generate a scalable model and compare legacy JSON with SQLite reports."""

from __future__ import annotations

import argparse
import gzip
import json
import re
import sqlite3
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from address_planner import (
    AddressSpace,
    Field,
    ReadOnly,
    ReadWrite,
    RegSpace,
    Register,
    SCHEMA_VERSION_V1,
    SCHEMA_VERSION_V2,
    decode_uint64,
    default_viewer_template_path,
    package_single_html,
)


def _positive(value: str) -> int:
    parsed = int(value)
    if parsed <= 0:
        raise argparse.ArgumentTypeError("value must be positive")
    return parsed


def _build_model(bank_count: int, registers_per_bank: int, fields_per_register: int):
    if fields_per_register > 32:
        raise ValueError("fields-per-register cannot exceed the 32-bit fixture width")
    register = Register("template", bit=32, description="standard control register")
    for field_index in range(fields_per_register):
        register.add(
            Field(
                f"field_{field_index}",
                bit=1,
                sw_access=ReadWrite if field_index % 2 == 0 else ReadOnly,
                hw_access=ReadOnly if field_index % 2 == 0 else ReadWrite,
                init_value=field_index % 2,
                description="repeated field description for address map metadata",
            ),
            offset=field_index,
        )

    bank_bytes = registers_per_bank * 4
    bank_stride = max(4096, bank_bytes)
    top = AddressSpace(
        "size_benchmark",
        bank_count * bank_stride,
        "large deterministic comparison model",
    )
    for bank_index in range(bank_count):
        bank = RegSpace(
            f"bank_{bank_index:03d}",
            bank_bytes,
            description="repeated register bank description",
        )
        for register_index in range(registers_per_bank):
            bank.add(register, register_index * 4, f"reg_{register_index:04d}")
        top.add(bank, bank_index * bank_stride)
    return top


def _semantic_counts(json_path: Path, database_path: Path) -> tuple[int, int]:
    roots = json.loads(json_path.read_text(encoding="utf-8"))
    json_nodes = []
    json_fields = []

    def visit(node, parent_id=None):
        node_id = len(json_nodes) + 1
        json_nodes.append(
            (
                node_id,
                parent_id,
                node["type"],
                node["name"],
                int(node["start_addr"], 16),
                int(node["end_addr"], 16),
                len(node.get("children", ())),
                len(node.get("fields", ())),
            )
        )
        for field in node.get("fields", ()):
            match = re.fullmatch(r"\[(\d+):(\d+)\]", field["Position"])
            if match is None:
                raise ValueError(f"unexpected legacy field position: {field['Position']}")
            msb, lsb = map(int, match.groups())
            json_fields.append(
                (
                    node_id,
                    field["name"],
                    lsb,
                    msb,
                    field["External"] == "True",
                    field["Software Access"],
                    field["Hardware Access"],
                    field["defaut_value"],
                    field["description"],
                )
            )
        for child in node.get("children", ()):
            visit(child, node_id)

    for root in roots:
        visit(root)

    connection = sqlite3.connect(str(database_path))
    connection.row_factory = sqlite3.Row
    try:
        metadata = dict(connection.execute("SELECT key, value FROM metadata"))
        access = json.loads(metadata["access_enum"])
        schema_version = int(metadata["schema_version"])
        if schema_version == SCHEMA_VERSION_V1:
            node_rows = connection.execute("SELECT * FROM nodes ORDER BY id")
            field_rows = connection.execute("SELECT * FROM fields ORDER BY id")
        elif schema_version == SCHEMA_VERSION_V2:
            node_rows = connection.execute(
                """
                SELECT occurrence.id, occurrence.parent_id, template.kind,
                       name.value AS name, occurrence.start_addr,
                       occurrence.end_addr, template.child_count,
                       template.field_count
                FROM node_occurrences AS occurrence
                JOIN node_templates AS template
                  ON template.id = occurrence.template_id
                JOIN texts AS name ON name.id = occurrence.name_text_id
                ORDER BY occurrence.id
                """
            )
            field_rows = connection.execute(
                """
                SELECT occurrence.id AS register_id, name.value AS name,
                       field.lsb, field.msb, field.external, field.sw_access,
                       field.hw_access, field.default_value,
                       description.value AS description
                FROM node_occurrences AS occurrence
                JOIN template_fields AS layout
                  ON layout.register_template_id = occurrence.template_id
                JOIN field_defs AS field ON field.id = layout.field_def_id
                JOIN texts AS name ON name.id = field.name_text_id
                JOIN texts AS description
                  ON description.id = field.description_text_id
                ORDER BY occurrence.id, layout.sort_order
                """
            )
        else:
            raise ValueError(f"unsupported benchmark schema: {schema_version}")
        sqlite_nodes = [
            (
                row["id"],
                row["parent_id"],
                "reg" if row["kind"] == 4 else "sys",
                row["name"],
                decode_uint64(row["start_addr"]),
                decode_uint64(row["end_addr"]),
                row["child_count"],
                row["field_count"],
            )
            for row in node_rows
        ]
        sqlite_fields = [
            (
                row["register_id"],
                row["name"],
                row["lsb"],
                row["msb"],
                bool(row["external"]),
                access[str(row["sw_access"])],
                access[str(row["hw_access"])],
                int.from_bytes(row["default_value"], "big"),
                row["description"],
            )
            for row in field_rows
        ]
    finally:
        connection.close()

    if json_nodes != sqlite_nodes:
        raise AssertionError("legacy JSON and SQLite node semantics differ")
    if json_fields != sqlite_fields:
        raise AssertionError("legacy JSON and SQLite Field semantics differ")
    return len(sqlite_nodes), len(sqlite_fields)


def _text_pool_metrics(database_path: Path) -> dict[str, int | None]:
    connection = sqlite3.connect(str(database_path))
    try:
        metadata = dict(connection.execute("SELECT key, value FROM metadata"))
        try:
            storage_bytes = connection.execute(
                """
                SELECT coalesce(sum(pgsize), 0) FROM dbstat
                WHERE name IN ('texts', 'sqlite_autoindex_texts_1')
                """
            ).fetchone()[0]
        except sqlite3.OperationalError:
            storage_bytes = None
    finally:
        connection.close()
    return {
        "unique_strings": int(metadata["text_count"]),
        "physical_references": int(metadata["text_reference_count"]),
        "logical_references": int(metadata["logical_text_reference_count"]),
        "unique_utf8_bytes": int(metadata["text_utf8_bytes"]),
        "logical_utf8_bytes": int(metadata["logical_text_utf8_bytes"]),
        "saved_utf8_bytes": int(metadata["text_utf8_saved_bytes"]),
        "sqlite_table_and_index_bytes": storage_bytes,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--banks", type=_positive, default=50)
    parser.add_argument("--registers-per-bank", type=_positive, default=200)
    parser.add_argument("--fields-per-register", type=_positive, default=8)
    args = parser.parse_args()

    started = time.perf_counter()
    model = _build_model(
        args.banks, args.registers_per_bank, args.fields_per_register
    )
    build_seconds = time.perf_counter() - started
    output = args.output.expanduser().resolve()
    model.path = str(output)
    model.report_json()
    html_dir = Path(model._html_dir)
    json_path = Path(model.json_path)
    v1_database_path = html_dir / "size_benchmark_address_map.v1.sqlite"
    v2_database_path = html_dir / "size_benchmark_address_map.sqlite"
    html_path = html_dir / "size_benchmark_address_map.html"
    v1_started = time.perf_counter()
    v1_database = model.report_sqlite(
        v1_database_path, schema_version=SCHEMA_VERSION_V1
    )
    v1_seconds = time.perf_counter() - v1_started
    v2_started = time.perf_counter()
    v2_database = model.report_sqlite(
        v2_database_path, schema_version=SCHEMA_VERSION_V2
    )
    v2_seconds = time.perf_counter() - v2_started
    packaged = package_single_html(
        v2_database.path,
        default_viewer_template_path(),
        html_path,
    )
    v1_counts = _semantic_counts(json_path, v1_database.path)
    v2_counts = _semantic_counts(json_path, v2_database.path)
    if v1_counts != v2_counts:
        raise AssertionError("schema v1 and v2 logical counts differ")
    compared_nodes, compared_fields = v2_counts

    json_bytes = json_path.read_bytes()
    result = {
        "model": {
            "banks": args.banks,
            "registers": args.banks * args.registers_per_bank,
            "fields": args.banks * args.registers_per_bank * args.fields_per_register,
            "build_seconds": round(build_seconds, 3),
        },
        "semantic_comparison": {
            "status": "PASS",
            "nodes": compared_nodes,
            "fields": compared_fields,
        },
        "database_counts": {
            "roots": v2_database.root_count,
            "nodes": v2_database.node_count,
            "fields": v2_database.field_count,
            "node_templates": int(v2_database.metadata["node_template_count"]),
            "field_definitions": int(
                v2_database.metadata["field_definition_count"]
            ),
            "texts": int(v2_database.metadata["text_count"]),
        },
        "generation_seconds": {
            "sqlite_v1": round(v1_seconds, 3),
            "sqlite_v2": round(v2_seconds, 3),
        },
        "text_pool": _text_pool_metrics(v2_database.path),
        "bytes": {
            "legacy_json": len(json_bytes),
            "legacy_json_gzip": len(
                gzip.compress(json_bytes, compresslevel=9, mtime=0)
            ),
            "sqlite_v1": v1_database.database_bytes,
            "sqlite_v1_gzip": len(
                gzip.compress(v1_database.path.read_bytes(), compresslevel=9, mtime=0)
            ),
            "sqlite_v2": v2_database.database_bytes,
            "sqlite_v2_gzip": packaged.compressed_database_bytes,
            "viewer_template": default_viewer_template_path().stat().st_size,
            "single_html_v2": packaged.html_bytes,
        },
    }
    report_path = output / "size_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, indent=2))
    print(report_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
