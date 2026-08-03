"""Deterministic, normalized SQLite reports for the address planner model.

The SQLite file is an intermediate artifact for the single-HTML viewer.  It
contains no recursively nested JSON: addressable objects reference their parent
and register fields reference their register.  This lets the viewer query one
expanded address space at a time.
"""

from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import stat
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping, Sequence

from .GlobalValues import FieldAccess


SCHEMA_VERSION_V1 = 1
SCHEMA_VERSION_V2 = 2
SUPPORTED_SCHEMA_VERSIONS = (SCHEMA_VERSION_V1, SCHEMA_VERSION_V2)

# Both writers are independently validated; v2 is the compact default.
# Keeping this as one public constant gives callers a discoverable compatibility flag:
# pass ``schema_version=SCHEMA_VERSION_V1`` to request the legacy layout.
SCHEMA_VERSION = SCHEMA_VERSION_V2
GENERATOR_VERSION_V1 = "address_planner.sqlite_report/1"
GENERATOR_VERSION_V2 = "address_planner.sqlite_report/2"
GENERATOR_VERSION = GENERATOR_VERSION_V2
VIEWER_MIN_VERSION_BY_SCHEMA = {
    SCHEMA_VERSION_V1: "1",
    SCHEMA_VERSION_V2: "2",
}
VIEWER_MIN_VERSION = VIEWER_MIN_VERSION_BY_SCHEMA[SCHEMA_VERSION]
SQLITE_APPLICATION_ID = 0x41505631  # ASCII "APV1"

NODE_KIND_ADDRESS_SPACE = 1
NODE_KIND_REG_SPACE = 2
# Reserved for a future model type that explicitly distinguishes Memory from a
# generic AddressSpace. The current object model has no such type, so the
# writer deliberately never guesses kind 3 from an empty AddressSpace.
NODE_KIND_MEMORY = 3
NODE_KIND_REGISTER = 4
NODE_KIND_NAMES = {
    NODE_KIND_ADDRESS_SPACE: "address_space",
    NODE_KIND_REG_SPACE: "reg_space",
    NODE_KIND_MEMORY: "memory_reserved",
    NODE_KIND_REGISTER: "register",
}

# This tuple is part of the Python/Viewer database contract.  The explicit
# expected names make an accidental re-order of FieldAccess fail immediately
# instead of silently changing the meaning of existing integer values.
FIELD_ACCESS_NAMES = (
    "Null",
    "ReadWrite",
    "ReadOnly",
    "ReadClean",
    "ReadSet",
    "WriteReadClean",
    "WriteReadSet",
    "WriteOnly",
    "WriteOnlyClean",
    "WriteOnlySet",
    "WriteClean",
    "WriteCleanReadSet",
    "Write1Clean",
    "Write1CleanReadSet",
    "Write0Clean",
    "Write0CleanReadSet",
    "WriteSet",
    "WriteSetReadClean",
    "Write1Set",
    "Write1SetReadClean",
    "Write0Set",
    "Write0SetReadClean",
    "Write1Toggle",
    "Write0Toggle",
    "WriteOnce",
    "WriteOnlyOnce",
    "Write1Pulse",
    "Write0Pulse",
)

FIELD_ACCESS_MEMBERS = tuple(FieldAccess)
if tuple(member.name for member in FIELD_ACCESS_MEMBERS) != FIELD_ACCESS_NAMES:
    raise RuntimeError(
        "FieldAccess declaration order changed; update the SQLite/Viewer schema "
        "contract deliberately before generating reports"
    )

FIELD_ACCESS_TO_CODE = {
    member: code for code, member in enumerate(FIELD_ACCESS_MEMBERS)
}
FIELD_ACCESS_CODE_BY_NAME = {
    member.name: code for member, code in FIELD_ACCESS_TO_CODE.items()
}
FIELD_ACCESS_NAME_BY_CODE = {
    code: member.name for member, code in FIELD_ACCESS_TO_CODE.items()
}
FIELD_ACCESS_VALUE_BY_CODE = {
    code: member.value for member, code in FIELD_ACCESS_TO_CODE.items()
}

UINT64_MAX = (1 << 64) - 1


def _metadata_json(values: Mapping[int, str]) -> str:
    """Encode integer-keyed schema mappings in a compact deterministic form."""

    return json.dumps(
        {str(key): values[key] for key in sorted(values)},
        ensure_ascii=True,
        separators=(",", ":"),
    )


ACCESS_ENUM_JSON = _metadata_json(FIELD_ACCESS_NAME_BY_CODE)
ACCESS_VALUE_ENUM_JSON = _metadata_json(FIELD_ACCESS_VALUE_BY_CODE)


V1_TABLE_SCHEMA_SQL = f"""
CREATE TABLE metadata (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE nodes (
    id            INTEGER PRIMARY KEY,
    parent_id     INTEGER REFERENCES nodes(id),
    kind          INTEGER NOT NULL CHECK(kind IN (1, 2, 3, 4)),
    sort_order    INTEGER NOT NULL CHECK(sort_order >= 0),
    name          TEXT NOT NULL,
    start_addr    BLOB NOT NULL
                  CHECK(typeof(start_addr) = 'blob' AND length(start_addr) = 8),
    end_addr      BLOB NOT NULL
                  CHECK(typeof(end_addr) = 'blob' AND length(end_addr) = 8),
    size_bytes    BLOB NOT NULL
                  CHECK(typeof(size_bytes) = 'blob' AND length(size_bytes) = 8),
    description   TEXT NOT NULL DEFAULT '',
    child_count   INTEGER NOT NULL DEFAULT 0 CHECK(child_count >= 0),
    field_count   INTEGER NOT NULL DEFAULT 0 CHECK(field_count >= 0)
);

CREATE TABLE fields (
    id             INTEGER PRIMARY KEY,
    register_id    INTEGER NOT NULL REFERENCES nodes(id),
    sort_order     INTEGER NOT NULL CHECK(sort_order >= 0),
    name           TEXT NOT NULL,
    lsb            INTEGER NOT NULL,
    msb            INTEGER NOT NULL,
    external       INTEGER NOT NULL DEFAULT 0,
    sw_access      INTEGER NOT NULL,
    hw_access      INTEGER NOT NULL,
    default_value  BLOB,
    description    TEXT NOT NULL DEFAULT '',
    CHECK(lsb >= 0),
    CHECK(msb >= lsb),
    CHECK(external IN (0, 1)),
    CHECK(sw_access BETWEEN 0 AND {len(FIELD_ACCESS_MEMBERS) - 1}),
    CHECK(hw_access BETWEEN 0 AND {len(FIELD_ACCESS_MEMBERS) - 1}),
    CHECK(default_value IS NULL OR typeof(default_value) = 'blob')
);

CREATE TABLE node_attributes (
    node_id  INTEGER NOT NULL REFERENCES nodes(id),
    key      TEXT NOT NULL,
    value    TEXT NOT NULL,
    PRIMARY KEY(node_id, key)
);
"""

V1_INDEX_SCHEMA_SQL = """
CREATE INDEX idx_nodes_parent_order
ON nodes(parent_id, sort_order, id);

CREATE INDEX idx_nodes_parent_address
ON nodes(parent_id, start_addr, id);

CREATE INDEX idx_nodes_name
ON nodes(name);

CREATE INDEX idx_fields_register_order
ON fields(register_id, sort_order, id);
"""

V1_REQUIRED_TABLES = frozenset(("metadata", "nodes", "fields", "node_attributes"))
V1_REQUIRED_INDEXES = frozenset(
    (
        "idx_nodes_parent_order",
        "idx_nodes_parent_address",
        "idx_nodes_name",
        "idx_fields_register_order",
    )
)


V2_TABLE_SCHEMA_SQL = f"""
CREATE TABLE metadata (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE texts (
    id     INTEGER PRIMARY KEY,
    value  TEXT NOT NULL UNIQUE
);

CREATE TABLE node_templates (
    id                         INTEGER PRIMARY KEY,
    content_hash               BLOB NOT NULL UNIQUE
                               CHECK(typeof(content_hash) = 'blob'
                                     AND length(content_hash) = 32),
    kind                       INTEGER NOT NULL CHECK(kind IN (1, 2, 3, 4)),
    size_bytes                 BLOB NOT NULL
                               CHECK(typeof(size_bytes) = 'blob'
                                     AND length(size_bytes) = 8),
    description_text_id INTEGER NOT NULL REFERENCES texts(id),
    child_count         INTEGER NOT NULL CHECK(child_count >= 0),
    field_count         INTEGER NOT NULL CHECK(field_count >= 0)
);

CREATE TABLE field_defs (
    id                  INTEGER PRIMARY KEY,
    content_hash        BLOB NOT NULL UNIQUE
                        CHECK(typeof(content_hash) = 'blob'
                              AND length(content_hash) = 32),
    name_text_id        INTEGER NOT NULL REFERENCES texts(id),
    lsb                 INTEGER NOT NULL CHECK(lsb >= 0),
    msb                 INTEGER NOT NULL CHECK(msb >= lsb),
    external            INTEGER NOT NULL CHECK(external IN (0, 1)),
    sw_access           INTEGER NOT NULL
                        CHECK(sw_access BETWEEN 0 AND {len(FIELD_ACCESS_MEMBERS) - 1}),
    hw_access           INTEGER NOT NULL
                        CHECK(hw_access BETWEEN 0 AND {len(FIELD_ACCESS_MEMBERS) - 1}),
    default_value       BLOB NOT NULL CHECK(typeof(default_value) = 'blob'),
    description_text_id INTEGER NOT NULL REFERENCES texts(id)
);

CREATE TABLE template_children (
    parent_template_id INTEGER NOT NULL REFERENCES node_templates(id),
    sort_order         INTEGER NOT NULL CHECK(sort_order >= 0),
    child_template_id  INTEGER NOT NULL REFERENCES node_templates(id),
    relative_addr      BLOB NOT NULL
                       CHECK(typeof(relative_addr) = 'blob'
                             AND length(relative_addr) = 8),
    child_name_text_id INTEGER NOT NULL REFERENCES texts(id),
    PRIMARY KEY(parent_template_id, sort_order)
) WITHOUT ROWID;

CREATE TABLE template_fields (
    register_template_id INTEGER NOT NULL REFERENCES node_templates(id),
    sort_order            INTEGER NOT NULL CHECK(sort_order >= 0),
    field_def_id          INTEGER NOT NULL REFERENCES field_defs(id),
    PRIMARY KEY(register_template_id, sort_order)
) WITHOUT ROWID;

CREATE TABLE node_occurrences (
    id           INTEGER PRIMARY KEY,
    parent_id    INTEGER REFERENCES node_occurrences(id),
    template_id  INTEGER NOT NULL REFERENCES node_templates(id),
    sort_order   INTEGER NOT NULL CHECK(sort_order >= 0),
    name_text_id INTEGER NOT NULL REFERENCES texts(id),
    start_addr   BLOB NOT NULL
                 CHECK(typeof(start_addr) = 'blob' AND length(start_addr) = 8),
    end_addr     BLOB NOT NULL
                 CHECK(typeof(end_addr) = 'blob' AND length(end_addr) = 8)
);
"""

V2_INDEX_SCHEMA_SQL = """
CREATE INDEX idx_occurrences_parent_order
ON node_occurrences(parent_id, sort_order, id);

CREATE INDEX idx_occurrences_address
ON node_occurrences(start_addr, end_addr, id);
"""

V2_REQUIRED_TABLES = frozenset(
    (
        "metadata",
        "texts",
        "node_templates",
        "field_defs",
        "template_children",
        "template_fields",
        "node_occurrences",
    )
)
V2_REQUIRED_INDEXES = frozenset(
    (
        "idx_occurrences_parent_order",
        "idx_occurrences_address",
    )
)


@dataclass(frozen=True)
class SQLiteReportInfo:
    """Description of a completed and validated SQLite report."""

    path: Path
    database_bytes: int
    sha256: str
    root_count: int
    node_count: int
    field_count: int
    metadata: Mapping[str, str]

    @property
    def schema_version(self) -> int:
        return int(self.metadata["schema_version"])

    @property
    def reuse_statistics(self) -> Mapping[str, int]:
        """Return v2 physical/logical reuse counters (empty for schema v1)."""

        keys = (
            "node_template_count",
            "node_template_reuse_count",
            "field_definition_count",
            "field_definition_reuse_count",
            "text_count",
            "text_reference_count",
            "logical_text_reference_count",
            "text_reuse_count",
            "text_utf8_bytes",
            "logical_text_utf8_bytes",
            "text_utf8_saved_bytes",
            "template_child_count",
            "template_field_count",
        )
        return {key: int(self.metadata[key]) for key in keys if key in self.metadata}


def encode_uint64(value: int) -> bytes:
    """Encode an unsigned 64-bit integer as an order-preserving BLOB."""

    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError("unsigned 64-bit value must be an integer")
    if value < 0 or value > UINT64_MAX:
        raise ValueError(f"unsigned 64-bit value out of range: {value!r}")
    return value.to_bytes(8, byteorder="big", signed=False)


def decode_uint64(value: bytes) -> int:
    """Decode a fixed-width SQLite address/size BLOB."""

    if not isinstance(value, bytes) or len(value) != 8:
        raise ValueError("unsigned 64-bit BLOB must contain exactly 8 bytes")
    return int.from_bytes(value, byteorder="big", signed=False)


def encode_uint_minimal(value: int) -> bytes:
    """Encode a non-negative integer using the minimum non-empty byte width."""

    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError("integer BLOB value must be an integer")
    if value < 0:
        raise ValueError("integer BLOB value cannot be negative")
    width = max(1, (value.bit_length() + 7) // 8)
    return value.to_bytes(width, byteorder="big", signed=False)


def _text(value, label: str) -> str:
    if value is None:
        return ""
    if not isinstance(value, str):
        raise TypeError(f"{label} must be text")
    return value


def _non_negative_int(value, label: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"{label} must be an integer")
    if value < 0:
        raise ValueError(f"{label} cannot be negative")
    return value


def _node_kind(node) -> int:
    # Imports stay local to avoid making this storage module part of the model's
    # already-deep import cycle.
    from .Reg import Register
    from .RegSpace import RegSpace

    if isinstance(node, Register):
        return NODE_KIND_REGISTER
    if isinstance(node, RegSpace):
        return NODE_KIND_REG_SPACE
    return NODE_KIND_ADDRESS_SPACE


def _node_range_bytes(node) -> tuple[int, int, int]:
    """Return (start, end, size) in bytes for any addressable model node."""

    from .Reg import Register

    global_start_bits = _non_negative_int(
        node.global_start_address, f"{node.module_name}.global_start_address"
    )
    if global_start_bits % 8:
        raise ValueError(
            f"{node.module_name}.global_start_address is not byte aligned: "
            f"{global_start_bits} bits"
        )
    start = global_start_bits // 8

    if isinstance(node, Register):
        width_bits = _non_negative_int(node.bit, f"{node.module_name}.bit")
        if width_bits == 0:
            raise ValueError(f"{node.module_name}.bit must be positive")
        size = (width_bits + 7) // 8
    else:
        size = _non_negative_int(node.size, f"{node.module_name}.size")
        if size == 0:
            raise ValueError(f"{node.module_name}.size must be positive")

    end = start + size - 1
    # Validate all three values now so failures happen before SQLite sees a
    # partial report.  The schema stores each one in the same uint64 format.
    encode_uint64(start)
    encode_uint64(end)
    encode_uint64(size)
    return start, end, size


def _sorted_children(node) -> list:
    children = list(getattr(node, "sub_space_list", ()))
    indexed = list(enumerate(children))
    try:
        indexed.sort(
            key=lambda pair: (
                _non_negative_int(pair[1].bit_offset, f"{pair[1].module_name}.bit_offset"),
                pair[0],
            )
        )
    except AttributeError as error:
        raise TypeError(
            f"{node.module_name}.sub_space_list contains a non-addressable object"
        ) from error
    return [child for _, child in indexed]


def _sorted_fields(node) -> list:
    from .Field import FilledField

    fields = [
        (index, field)
        for index, field in enumerate(getattr(node, "field_list", ()))
        if not isinstance(field, FilledField)
    ]
    fields.sort(
        key=lambda pair: (
            _non_negative_int(pair[1].bit_offset, f"{pair[1].name}.bit_offset"),
            pair[0],
        )
    )
    return [field for _, field in fields]


def _node_attributes(node, kind: int) -> list[tuple[str, str]]:
    attributes = {}
    if kind in (NODE_KIND_REG_SPACE, NODE_KIND_REGISTER):
        if hasattr(node, "bus_width"):
            attributes["bus_width"] = str(node.bus_width)
        if hasattr(node, "software_interface"):
            attributes["software_interface"] = str(node.software_interface)
    if kind == NODE_KIND_REGISTER:
        attributes["width_bits"] = str(node.bit)
        reg_type = getattr(node, "reg_type", None)
        if reg_type is not None:
            attributes["register_type"] = getattr(reg_type, "name", str(reg_type))
        attributes["parity"] = "1" if bool(getattr(node, "parity", False)) else "0"
        attributes["reset_domain"] = str(getattr(node, "rst_domain", ""))
    return sorted(attributes.items())


class _V1ModelWriter:
    def __init__(self, connection: sqlite3.Connection):
        self.connection = connection
        self.next_node_id = 1
        self.next_field_id = 1
        self.seen_nodes = set()

    @property
    def node_count(self) -> int:
        return self.next_node_id - 1

    @property
    def field_count(self) -> int:
        return self.next_field_id - 1

    def write_node(self, node, parent_id, sort_order: int) -> None:
        from .AddressSpace import AddressSpace

        if not isinstance(node, AddressSpace):
            raise TypeError("SQLite report roots and children must be AddressSpace objects")
        identity = id(node)
        if identity in self.seen_nodes:
            raise ValueError(
                f"address model is cyclic or reuses node object {node.module_name!r}"
            )
        self.seen_nodes.add(identity)

        node_id = self.next_node_id
        self.next_node_id += 1
        kind = _node_kind(node)
        children = _sorted_children(node)
        fields = _sorted_fields(node) if kind == NODE_KIND_REGISTER else []
        start, end, size = _node_range_bytes(node)

        self.connection.execute(
            """
            INSERT INTO nodes(
                id, parent_id, kind, sort_order, name, start_addr, end_addr,
                size_bytes, description, child_count, field_count
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                node_id,
                parent_id,
                kind,
                sort_order,
                _text(node.module_name, "node.module_name"),
                encode_uint64(start),
                encode_uint64(end),
                encode_uint64(size),
                _text(node.description, f"{node.module_name}.description"),
                len(children),
                len(fields),
            ),
        )

        attributes = _node_attributes(node, kind)
        if attributes:
            self.connection.executemany(
                "INSERT INTO node_attributes(node_id, key, value) VALUES (?, ?, ?)",
                ((node_id, key, value) for key, value in attributes),
            )

        for field_order, field in enumerate(fields):
            self.write_field(field, node_id, field_order)
        for child_order, child in enumerate(children):
            self.write_node(child, node_id, child_order)

    def write_field(self, field, register_id: int, sort_order: int) -> None:
        field_id = self.next_field_id
        self.next_field_id += 1
        lsb = _non_negative_int(field.start_bit, f"{field.name}.start_bit")
        msb = _non_negative_int(field.end_bit, f"{field.name}.end_bit")
        if msb < lsb:
            raise ValueError(f"{field.name}.end_bit cannot be below start_bit")
        try:
            sw_access = FIELD_ACCESS_TO_CODE[field.sw_access]
            hw_access = FIELD_ACCESS_TO_CODE[field.hw_access]
        except KeyError as error:
            raise ValueError(f"{field.name} uses an unknown FieldAccess value") from error

        default_value = encode_uint_minimal(
            _non_negative_int(field.init_value, f"{field.name}.init_value")
        )
        self.connection.execute(
            """
            INSERT INTO fields(
                id, register_id, sort_order, name, lsb, msb, external,
                sw_access, hw_access, default_value, description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                field_id,
                register_id,
                sort_order,
                _text(field.name, "field.name"),
                lsb,
                msb,
                1 if bool(field.is_external) else 0,
                sw_access,
                hw_access,
                default_value,
                _text(field.description, f"{field.name}.description"),
            ),
        )


def _normalise_roots(roots) -> tuple:
    from .AddressSpace import AddressSpace

    if isinstance(roots, AddressSpace):
        result = (roots,)
    elif isinstance(roots, Sequence) and not isinstance(roots, (str, bytes, bytearray)):
        result = tuple(roots)
    else:
        raise TypeError("roots must be an AddressSpace or an ordered sequence of them")
    if not result:
        raise ValueError("SQLite report must contain at least one root AddressSpace")
    if not all(isinstance(root, AddressSpace) for root in result):
        raise TypeError("SQLite report roots must all be AddressSpace objects")
    return result


def _v1_metadata_rows(
    *, model_name: str, root_count: int, node_count: int, field_count: int
) -> tuple[tuple[str, str], ...]:
    return (
        ("schema_version", str(SCHEMA_VERSION_V1)),
        ("generator_version", GENERATOR_VERSION_V1),
        ("viewer_min_version", VIEWER_MIN_VERSION_BY_SCHEMA[SCHEMA_VERSION_V1]),
        ("model_name", model_name),
        ("root_count", str(root_count)),
        ("node_count", str(node_count)),
        ("field_count", str(field_count)),
        ("access_enum", ACCESS_ENUM_JSON),
        ("access_value_enum", ACCESS_VALUE_ENUM_JSON),
    )


def _configure_build_connection(
    connection: sqlite3.Connection, schema_version: int
) -> None:
    connection.execute("PRAGMA journal_mode = OFF")
    connection.execute("PRAGMA synchronous = OFF")
    connection.execute("PRAGMA temp_store = MEMORY")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute(f"PRAGMA application_id = {SQLITE_APPLICATION_ID}")
    connection.execute(f"PRAGMA user_version = {schema_version}")


def _read_metadata(connection: sqlite3.Connection) -> dict[str, str]:
    return dict(connection.execute("SELECT key, value FROM metadata ORDER BY key"))


def _file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _publication_mode(target: Path) -> int:
    """Preserve an existing report mode, otherwise publish a readable file."""

    try:
        return stat.S_IMODE(target.stat().st_mode)
    except FileNotFoundError:
        return 0o644


def _validate_v1_connection(
    connection: sqlite3.Connection,
) -> tuple[dict[str, str], int, int, int]:
    integrity_rows = [row[0] for row in connection.execute("PRAGMA integrity_check")]
    if integrity_rows != ["ok"]:
        raise ValueError(f"SQLite integrity_check failed: {integrity_rows!r}")
    foreign_key_rows = list(connection.execute("PRAGMA foreign_key_check"))
    if foreign_key_rows:
        raise ValueError(f"SQLite foreign_key_check failed: {foreign_key_rows!r}")

    application_id = connection.execute("PRAGMA application_id").fetchone()[0]
    if application_id != SQLITE_APPLICATION_ID:
        raise ValueError(f"unexpected SQLite application_id: {application_id}")
    user_version = connection.execute("PRAGMA user_version").fetchone()[0]
    if user_version != SCHEMA_VERSION_V1:
        raise ValueError(f"unexpected SQLite user_version: {user_version}")

    objects = dict(
        connection.execute(
            "SELECT name, type FROM sqlite_master WHERE type IN ('table', 'index')"
        )
    )
    missing_tables = V1_REQUIRED_TABLES.difference(objects)
    missing_indexes = V1_REQUIRED_INDEXES.difference(objects)
    if missing_tables or missing_indexes:
        raise ValueError(
            f"SQLite report schema is incomplete; tables={sorted(missing_tables)}, "
            f"indexes={sorted(missing_indexes)}"
        )

    metadata = _read_metadata(connection)
    required_metadata = {
        "schema_version",
        "generator_version",
        "viewer_min_version",
        "model_name",
        "root_count",
        "node_count",
        "field_count",
        "access_enum",
        "access_value_enum",
    }
    missing_metadata = required_metadata.difference(metadata)
    if missing_metadata:
        raise ValueError(f"SQLite report metadata missing: {sorted(missing_metadata)}")
    if metadata["schema_version"] != str(SCHEMA_VERSION_V1):
        raise ValueError("metadata schema_version does not match the database schema")
    if metadata["access_enum"] != ACCESS_ENUM_JSON:
        raise ValueError("metadata access_enum does not match the schema contract")
    if metadata["access_value_enum"] != ACCESS_VALUE_ENUM_JSON:
        raise ValueError("metadata access_value_enum does not match the schema contract")

    root_count = connection.execute(
        "SELECT count(*) FROM nodes WHERE parent_id IS NULL"
    ).fetchone()[0]
    node_count = connection.execute("SELECT count(*) FROM nodes").fetchone()[0]
    field_count = connection.execute("SELECT count(*) FROM fields").fetchone()[0]
    actual_counts = (root_count, node_count, field_count)
    recorded_counts = tuple(
        int(metadata[key]) for key in ("root_count", "node_count", "field_count")
    )
    if actual_counts != recorded_counts:
        raise ValueError(
            f"SQLite report metadata counts {recorded_counts!r} do not match "
            f"database counts {actual_counts!r}"
        )

    incorrect_children = connection.execute(
        """
        SELECT id FROM nodes
        WHERE child_count != (
            SELECT count(*) FROM nodes AS child WHERE child.parent_id = nodes.id
        )
        LIMIT 1
        """
    ).fetchone()
    if incorrect_children:
        raise ValueError(f"node {incorrect_children[0]} has an incorrect child_count")
    incorrect_fields = connection.execute(
        """
        SELECT id FROM nodes
        WHERE field_count != (
            SELECT count(*) FROM fields WHERE fields.register_id = nodes.id
        )
        LIMIT 1
        """
    ).fetchone()
    if incorrect_fields:
        raise ValueError(f"node {incorrect_fields[0]} has an incorrect field_count")
    invalid_field_parent = connection.execute(
        """
        SELECT fields.id FROM fields
        JOIN nodes ON nodes.id = fields.register_id
        WHERE nodes.kind != ? LIMIT 1
        """,
        (NODE_KIND_REGISTER,),
    ).fetchone()
    if invalid_field_parent:
        raise ValueError(
            f"field {invalid_field_parent[0]} belongs to a non-register node"
        )

    cursor = connection.execute("SELECT id, start_addr, end_addr, size_bytes FROM nodes")
    while True:
        rows = cursor.fetchmany(1024)
        if not rows:
            break
        for node_id, start_blob, end_blob, size_blob in rows:
            start = decode_uint64(start_blob)
            end = decode_uint64(end_blob)
            size = decode_uint64(size_blob)
            if size == 0 or end != start + size - 1:
                raise ValueError(f"node {node_id} has an inconsistent address range")

    return metadata, root_count, node_count, field_count


def _canonical_blob(value: bytes) -> bytes:
    """Length-prefix bytes so canonical records cannot be concatenation-ambiguous."""

    return encode_uint64(len(value)) + value


def _canonical_text(value: str) -> bytes:
    return _canonical_blob(value.encode("utf-8"))


def _content_hash(canonical: bytes) -> bytes:
    """Return the content-address used by schema v2.

    This small seam is intentionally separate from record construction: tests
    can force a collision and prove that canonical-byte comparison, rather than
    SHA-256 probability, protects deduplication.
    """

    return hashlib.sha256(canonical).digest()


def _v2_field_canonical(
    *,
    name: str,
    lsb: int,
    msb: int,
    external: int,
    sw_access: int,
    hw_access: int,
    default_value: bytes,
    description: str,
) -> bytes:
    return b"".join(
        (
            _canonical_blob(b"address_planner/field/v2"),
            _canonical_text(name),
            encode_uint64(lsb),
            encode_uint64(msb),
            encode_uint64(external),
            encode_uint64(sw_access),
            encode_uint64(hw_access),
            _canonical_blob(default_value),
            _canonical_text(description),
        )
    )


def _v2_node_canonical(
    *,
    kind: int,
    size_bytes: int,
    description: str,
    children: Sequence[tuple[str, int, bytes]],
    field_hashes: Sequence[bytes],
) -> bytes:
    parts = [
        _canonical_blob(b"address_planner/node-template/v2"),
        encode_uint64(kind),
        encode_uint64(size_bytes),
        _canonical_text(description),
        encode_uint64(len(children)),
    ]
    for child_name, relative_addr, child_hash in children:
        parts.extend(
            (
                _canonical_text(child_name),
                encode_uint64(relative_addr),
                _canonical_blob(child_hash),
            )
        )
    parts.append(encode_uint64(len(field_hashes)))
    parts.extend(_canonical_blob(field_hash) for field_hash in field_hashes)
    return b"".join(parts)


@dataclass(frozen=True)
class _V2FieldDefinition:
    content_hash: bytes
    canonical: bytes
    name: str
    lsb: int
    msb: int
    external: int
    sw_access: int
    hw_access: int
    default_value: bytes
    description: str


@dataclass(frozen=True)
class _V2TemplateChild:
    sort_order: int
    child_hash: bytes
    relative_addr: int
    child_name: str


@dataclass(frozen=True)
class _V2NodeTemplate:
    content_hash: bytes
    canonical: bytes
    kind: int
    size_bytes: int
    description: str
    children: tuple[_V2TemplateChild, ...]
    field_hashes: tuple[bytes, ...]


@dataclass(frozen=True)
class _V2Occurrence:
    id: int
    parent_id: int | None
    template_hash: bytes
    sort_order: int
    name: str
    start_addr: int
    end_addr: int


class _V2Model:
    """In-memory content-addressed projection built before SQLite is touched."""

    def __init__(self, roots: tuple):
        self.roots = roots
        self.field_definitions: dict[bytes, _V2FieldDefinition] = {}
        self.node_templates: dict[bytes, _V2NodeTemplate] = {}
        self.occurrences: list[_V2Occurrence] = []
        self.texts: set[str] = set()
        self.field_count = 0
        self._seen_template_nodes: set[int] = set()
        self._seen_occurrence_nodes: set[int] = set()
        # This is only a traversal memo. Persistent template identity is always
        # the canonical content hash, never Python object identity.
        self._node_template_hash_by_identity: dict[int, bytes] = {}

    @classmethod
    def build(cls, roots: tuple) -> "_V2Model":
        model = cls(roots)
        for root in roots:
            model._build_template(root)
        for root_order, root in enumerate(roots):
            model._build_occurrence(root, None, root_order)
        return model

    @property
    def node_count(self) -> int:
        return len(self.occurrences)

    @property
    def root_count(self) -> int:
        return len(self.roots)

    @property
    def template_child_count(self) -> int:
        return sum(len(template.children) for template in self.node_templates.values())

    @property
    def template_field_count(self) -> int:
        return sum(
            len(template.field_hashes) for template in self.node_templates.values()
        )

    @property
    def text_reference_count(self) -> int:
        # These are physical v2 foreign-key references, not expanded logical
        # references. Keeping both numbers in metadata makes the pool's actual
        # cost and its logical reuse independently measurable.
        return (
            self.node_count
            + len(self.node_templates)
            + self.template_child_count
            + 2 * len(self.field_definitions)
        )

    @property
    def text_utf8_bytes(self) -> int:
        return sum(len(value.encode("utf-8")) for value in self.texts)

    @property
    def logical_text_utf8_bytes(self) -> int:
        total = 0
        for occurrence in self.occurrences:
            template = self.node_templates[occurrence.template_hash]
            total += len(occurrence.name.encode("utf-8"))
            total += len(template.description.encode("utf-8"))
            for field_hash in template.field_hashes:
                definition = self.field_definitions[field_hash]
                total += len(definition.name.encode("utf-8"))
                total += len(definition.description.encode("utf-8"))
        return total

    def _intern_field(self, field) -> bytes:
        lsb = _non_negative_int(field.start_bit, f"{field.name}.start_bit")
        msb = _non_negative_int(field.end_bit, f"{field.name}.end_bit")
        if msb < lsb:
            raise ValueError(f"{field.name}.end_bit cannot be below start_bit")
        # Canonical integers are uint64 even though practical Field positions
        # are much smaller and use SQLite INTEGER for direct Viewer queries.
        encode_uint64(lsb)
        encode_uint64(msb)
        if lsb > (1 << 63) - 1 or msb > (1 << 63) - 1:
            raise ValueError(f"{field.name} bit position exceeds SQLite INTEGER range")
        try:
            sw_access = FIELD_ACCESS_TO_CODE[field.sw_access]
            hw_access = FIELD_ACCESS_TO_CODE[field.hw_access]
        except KeyError as error:
            raise ValueError(f"{field.name} uses an unknown FieldAccess value") from error

        name = _text(field.name, "field.name")
        description = _text(field.description, f"{field.name}.description")
        external = 1 if bool(field.is_external) else 0
        default_value = encode_uint_minimal(
            _non_negative_int(field.init_value, f"{field.name}.init_value")
        )
        canonical = _v2_field_canonical(
            name=name,
            lsb=lsb,
            msb=msb,
            external=external,
            sw_access=sw_access,
            hw_access=hw_access,
            default_value=default_value,
            description=description,
        )
        content_hash = _content_hash(canonical)
        if not isinstance(content_hash, bytes) or len(content_hash) != 32:
            raise ValueError("content hash function must return exactly 32 bytes")
        existing = self.field_definitions.get(content_hash)
        if existing is not None:
            if existing.canonical != canonical:
                raise ValueError(
                    "SHA-256 collision between distinct canonical Field definitions"
                )
            return content_hash

        record = _V2FieldDefinition(
            content_hash=content_hash,
            canonical=canonical,
            name=name,
            lsb=lsb,
            msb=msb,
            external=external,
            sw_access=sw_access,
            hw_access=hw_access,
            default_value=default_value,
            description=description,
        )
        self.field_definitions[content_hash] = record
        self.texts.update((name, description))
        return content_hash

    def _build_template(self, node) -> bytes:
        from .AddressSpace import AddressSpace

        if not isinstance(node, AddressSpace):
            raise TypeError("SQLite report roots and children must be AddressSpace objects")
        identity = id(node)
        if identity in self._seen_template_nodes:
            raise ValueError(
                f"address model is cyclic or reuses node object {node.module_name!r}"
            )
        self._seen_template_nodes.add(identity)

        kind = _node_kind(node)
        _, _, size = _node_range_bytes(node)
        description = _text(node.description, f"{node.module_name}.description")
        fields = _sorted_fields(node) if kind == NODE_KIND_REGISTER else []
        field_hashes = tuple(self._intern_field(field) for field in fields)
        self.field_count += len(fields)

        children = []
        for child_order, child in enumerate(_sorted_children(node)):
            child_hash = self._build_template(child)
            relative_bits = _non_negative_int(
                child.bit_offset, f"{child.module_name}.bit_offset"
            )
            if relative_bits % 8:
                raise ValueError(
                    f"{child.module_name}.bit_offset is not byte aligned: "
                    f"{relative_bits} bits"
                )
            relative_addr = relative_bits // 8
            encode_uint64(relative_addr)
            child_name = _text(child.module_name, "child.module_name")
            children.append(
                _V2TemplateChild(
                    sort_order=child_order,
                    child_hash=child_hash,
                    relative_addr=relative_addr,
                    child_name=child_name,
                )
            )
            self.texts.add(child_name)

        canonical = _v2_node_canonical(
            kind=kind,
            size_bytes=size,
            description=description,
            children=tuple(
                (child.child_name, child.relative_addr, child.child_hash)
                for child in children
            ),
            field_hashes=field_hashes,
        )
        content_hash = _content_hash(canonical)
        if not isinstance(content_hash, bytes) or len(content_hash) != 32:
            raise ValueError("content hash function must return exactly 32 bytes")
        existing = self.node_templates.get(content_hash)
        if existing is not None:
            if existing.canonical != canonical:
                raise ValueError(
                    "SHA-256 collision between distinct canonical node templates"
                )
            self._node_template_hash_by_identity[identity] = content_hash
            return content_hash

        self.node_templates[content_hash] = _V2NodeTemplate(
            content_hash=content_hash,
            canonical=canonical,
            kind=kind,
            size_bytes=size,
            description=description,
            children=tuple(children),
            field_hashes=field_hashes,
        )
        self._node_template_hash_by_identity[identity] = content_hash
        self.texts.add(description)
        return content_hash

    def _build_occurrence(self, node, parent_id: int | None, sort_order: int) -> None:
        identity = id(node)
        if identity in self._seen_occurrence_nodes:
            raise ValueError(
                f"address model is cyclic or reuses node object {node.module_name!r}"
            )
        self._seen_occurrence_nodes.add(identity)
        node_id = len(self.occurrences) + 1
        start, end, _ = _node_range_bytes(node)

        template_hash = self._template_hash_for_occurrence(node)
        name = _text(node.module_name, "node.module_name")
        self.texts.add(name)
        self.occurrences.append(
            _V2Occurrence(
                id=node_id,
                parent_id=parent_id,
                template_hash=template_hash,
                sort_order=sort_order,
                name=name,
                start_addr=start,
                end_addr=end,
            )
        )
        for child_order, child in enumerate(_sorted_children(node)):
            self._build_occurrence(child, node_id, child_order)

    def _template_hash_for_occurrence(self, node) -> bytes:
        """Resolve the traversal memo; the returned persistent ID is content based."""

        try:
            return self._node_template_hash_by_identity[id(node)]
        except KeyError as error:
            raise ValueError("occurrence does not resolve to a known template") from error


V2_COUNT_METADATA_KEYS = (
    "root_count",
    "node_count",
    "field_count",
    "node_template_count",
    "node_template_reuse_count",
    "field_definition_count",
    "field_definition_reuse_count",
    "text_count",
    "text_reference_count",
    "logical_text_reference_count",
    "text_reuse_count",
    "text_utf8_bytes",
    "logical_text_utf8_bytes",
    "text_utf8_saved_bytes",
    "template_child_count",
    "template_field_count",
)


def _validate_v2_connection(
    connection: sqlite3.Connection,
) -> tuple[dict[str, str], int, int, int]:
    integrity_rows = [row[0] for row in connection.execute("PRAGMA integrity_check")]
    if integrity_rows != ["ok"]:
        raise ValueError(f"SQLite integrity_check failed: {integrity_rows!r}")
    foreign_key_rows = list(connection.execute("PRAGMA foreign_key_check"))
    if foreign_key_rows:
        raise ValueError(f"SQLite foreign_key_check failed: {foreign_key_rows!r}")

    application_id = connection.execute("PRAGMA application_id").fetchone()[0]
    if application_id != SQLITE_APPLICATION_ID:
        raise ValueError(f"unexpected SQLite application_id: {application_id}")
    user_version = connection.execute("PRAGMA user_version").fetchone()[0]
    if user_version != SCHEMA_VERSION_V2:
        raise ValueError(f"unexpected SQLite user_version: {user_version}")

    objects = dict(
        connection.execute(
            "SELECT name, type FROM sqlite_master WHERE type IN ('table', 'index')"
        )
    )
    missing_tables = V2_REQUIRED_TABLES.difference(objects)
    missing_indexes = V2_REQUIRED_INDEXES.difference(objects)
    if missing_tables or missing_indexes:
        raise ValueError(
            f"SQLite report schema is incomplete; tables={sorted(missing_tables)}, "
            f"indexes={sorted(missing_indexes)}"
        )

    metadata = _read_metadata(connection)
    required_metadata = {
        "schema_version",
        "generator_version",
        "viewer_min_version",
        "model_name",
        "access_enum",
        "access_value_enum",
        *V2_COUNT_METADATA_KEYS,
    }
    missing_metadata = required_metadata.difference(metadata)
    if missing_metadata:
        raise ValueError(f"SQLite report metadata missing: {sorted(missing_metadata)}")
    if metadata["schema_version"] != str(SCHEMA_VERSION_V2):
        raise ValueError("metadata schema_version does not match the database schema")
    if metadata["generator_version"] != GENERATOR_VERSION_V2:
        raise ValueError("metadata generator_version does not match schema v2")
    if metadata["viewer_min_version"] != VIEWER_MIN_VERSION_BY_SCHEMA[SCHEMA_VERSION_V2]:
        raise ValueError("metadata viewer_min_version does not match schema v2")
    if metadata["access_enum"] != ACCESS_ENUM_JSON:
        raise ValueError("metadata access_enum does not match the schema contract")
    if metadata["access_value_enum"] != ACCESS_VALUE_ENUM_JSON:
        raise ValueError("metadata access_value_enum does not match the schema contract")
    try:
        recorded = {key: int(metadata[key]) for key in V2_COUNT_METADATA_KEYS}
    except ValueError as error:
        raise ValueError("schema v2 count metadata must contain decimal integers") from error
    if any(value < 0 for value in recorded.values()):
        raise ValueError("schema v2 count metadata cannot be negative")

    root_count = connection.execute(
        "SELECT count(*) FROM node_occurrences WHERE parent_id IS NULL"
    ).fetchone()[0]
    node_count = connection.execute("SELECT count(*) FROM node_occurrences").fetchone()[0]
    field_count = connection.execute(
        """
        SELECT coalesce(sum(node_templates.field_count), 0)
        FROM node_occurrences
        JOIN node_templates ON node_templates.id = node_occurrences.template_id
        """
    ).fetchone()[0]
    node_template_count = connection.execute(
        "SELECT count(*) FROM node_templates"
    ).fetchone()[0]
    field_definition_count = connection.execute(
        "SELECT count(*) FROM field_defs"
    ).fetchone()[0]
    text_count = connection.execute("SELECT count(*) FROM texts").fetchone()[0]
    template_child_count = connection.execute(
        "SELECT count(*) FROM template_children"
    ).fetchone()[0]
    template_field_count = connection.execute(
        "SELECT count(*) FROM template_fields"
    ).fetchone()[0]
    text_reference_count = (
        node_count
        + node_template_count
        + template_child_count
        + 2 * field_definition_count
    )
    logical_text_reference_count = 2 * (node_count + field_count)
    text_utf8_bytes = sum(
        len(value.encode("utf-8"))
        for (value,) in connection.execute("SELECT value FROM texts")
    )
    logical_text_utf8_bytes = sum(
        len(name.encode("utf-8")) + len(description.encode("utf-8"))
        for name, description in connection.execute(
            """
            SELECT name.value, description.value
            FROM node_occurrences AS occurrence
            JOIN node_templates AS template
              ON template.id = occurrence.template_id
            JOIN texts AS name ON name.id = occurrence.name_text_id
            JOIN texts AS description
              ON description.id = template.description_text_id
            """
        )
    )
    logical_text_utf8_bytes += sum(
        occurrence_count
        * (len(name.encode("utf-8")) + len(description.encode("utf-8")))
        for name, description, occurrence_count in connection.execute(
            """
            SELECT name.value, description.value, count(occurrence.id)
            FROM template_fields AS layout
            JOIN field_defs AS field ON field.id = layout.field_def_id
            JOIN texts AS name ON name.id = field.name_text_id
            JOIN texts AS description
              ON description.id = field.description_text_id
            JOIN node_occurrences AS occurrence
              ON occurrence.template_id = layout.register_template_id
            GROUP BY layout.register_template_id, layout.sort_order
            """
        )
    )
    expected = {
        "root_count": root_count,
        "node_count": node_count,
        "field_count": field_count,
        "node_template_count": node_template_count,
        "node_template_reuse_count": node_count - node_template_count,
        "field_definition_count": field_definition_count,
        "field_definition_reuse_count": field_count - field_definition_count,
        "text_count": text_count,
        "text_reference_count": text_reference_count,
        "logical_text_reference_count": logical_text_reference_count,
        "text_reuse_count": logical_text_reference_count - text_count,
        "text_utf8_bytes": text_utf8_bytes,
        "logical_text_utf8_bytes": logical_text_utf8_bytes,
        "text_utf8_saved_bytes": logical_text_utf8_bytes - text_utf8_bytes,
        "template_child_count": template_child_count,
        "template_field_count": template_field_count,
    }
    if recorded != expected:
        raise ValueError(
            f"SQLite report metadata counts {recorded!r} do not match "
            f"database counts {expected!r}"
        )

    incorrect_children = connection.execute(
        """
        SELECT node_templates.id FROM node_templates
        WHERE child_count != (
            SELECT count(*) FROM template_children
            WHERE parent_template_id = node_templates.id
        ) LIMIT 1
        """
    ).fetchone()
    if incorrect_children:
        raise ValueError(
            f"node template {incorrect_children[0]} has an incorrect child_count"
        )
    incorrect_fields = connection.execute(
        """
        SELECT node_templates.id FROM node_templates
        WHERE field_count != (
            SELECT count(*) FROM template_fields
            WHERE register_template_id = node_templates.id
        ) LIMIT 1
        """
    ).fetchone()
    if incorrect_fields:
        raise ValueError(
            f"node template {incorrect_fields[0]} has an incorrect field_count"
        )
    invalid_field_template = connection.execute(
        """
        SELECT template_fields.register_template_id
        FROM template_fields
        JOIN node_templates
          ON node_templates.id = template_fields.register_template_id
        WHERE node_templates.kind != ? LIMIT 1
        """,
        (NODE_KIND_REGISTER,),
    ).fetchone()
    if invalid_field_template:
        raise ValueError(
            f"non-register template {invalid_field_template[0]} owns Field definitions"
        )
    orphan_template = connection.execute(
        """
        SELECT id FROM node_templates
        EXCEPT
        SELECT template_id FROM node_occurrences
        LIMIT 1
        """
    ).fetchone()
    if orphan_template:
        raise ValueError(f"node template {orphan_template[0]} is not instantiated")
    orphan_field = connection.execute(
        """
        SELECT id FROM field_defs
        EXCEPT
        SELECT field_def_id FROM template_fields
        LIMIT 1
        """
    ).fetchone()
    if orphan_field:
        raise ValueError(f"Field definition {orphan_field[0]} is not referenced")

    text_by_id = dict(connection.execute("SELECT id, value FROM texts ORDER BY id"))
    field_hash_by_id = {}
    for row in connection.execute(
        """
        SELECT id, content_hash, name_text_id, lsb, msb, external,
               sw_access, hw_access, default_value, description_text_id
        FROM field_defs ORDER BY id
        """
    ):
        (
            field_id,
            stored_hash,
            name_text_id,
            lsb,
            msb,
            external,
            sw_access,
            hw_access,
            default_value,
            description_text_id,
        ) = row
        canonical = _v2_field_canonical(
            name=text_by_id[name_text_id],
            lsb=lsb,
            msb=msb,
            external=external,
            sw_access=sw_access,
            hw_access=hw_access,
            default_value=default_value,
            description=text_by_id[description_text_id],
        )
        if _content_hash(canonical) != stored_hash:
            raise ValueError(f"Field definition {field_id} has an invalid content_hash")
        field_hash_by_id[field_id] = stored_hash

    templates = {
        row[0]: row[1:]
        for row in connection.execute(
            """
            SELECT id, content_hash, kind, size_bytes, description_text_id,
                   child_count, field_count
            FROM node_templates ORDER BY id
            """
        )
    }
    children_by_template: dict[int, list[tuple]] = {}
    for row in connection.execute(
        """
        SELECT parent_template_id, sort_order, child_template_id,
               relative_addr, child_name_text_id
        FROM template_children ORDER BY parent_template_id, sort_order
        """
    ):
        children_by_template.setdefault(row[0], []).append(row[1:])
    fields_by_template: dict[int, list[tuple[int, int]]] = {}
    for parent_id, sort_order, field_def_id in connection.execute(
        """
        SELECT register_template_id, sort_order, field_def_id
        FROM template_fields ORDER BY register_template_id, sort_order
        """
    ):
        fields_by_template.setdefault(parent_id, []).append((sort_order, field_def_id))

    verified_template_hashes: dict[int, bytes] = {}
    active_templates: set[int] = set()

    def verify_template(template_id: int) -> bytes:
        cached = verified_template_hashes.get(template_id)
        if cached is not None:
            return cached
        if template_id in active_templates:
            raise ValueError("node template graph contains a cycle")
        active_templates.add(template_id)
        (
            stored_hash,
            kind,
            size_blob,
            description_text_id,
            child_count,
            template_field_count_value,
        ) = templates[template_id]
        size_bytes = decode_uint64(size_blob)
        child_values = []
        child_rows = children_by_template.get(template_id, [])
        if [row[0] for row in child_rows] != list(range(child_count)):
            raise ValueError(f"node template {template_id} child order is not contiguous")
        previous_relative = None
        for sort_order, child_template_id, relative_blob, child_name_text_id in child_rows:
            relative_addr = decode_uint64(relative_blob)
            if previous_relative is not None and relative_addr < previous_relative:
                raise ValueError(
                    f"node template {template_id} children are not address sorted"
                )
            previous_relative = relative_addr
            # The legacy fluent DSL and MultiPort views can intentionally place
            # a logical child outside its parent's nominal size. Schema v2 must
            # preserve that visible v1/JSON placement rather than introduce a
            # new containment rule here.
            child_values.append(
                (
                    text_by_id[child_name_text_id],
                    relative_addr,
                    verify_template(child_template_id),
                )
            )
        field_rows = fields_by_template.get(template_id, [])
        if [row[0] for row in field_rows] != list(range(template_field_count_value)):
            raise ValueError(f"node template {template_id} Field order is not contiguous")
        canonical = _v2_node_canonical(
            kind=kind,
            size_bytes=size_bytes,
            description=text_by_id[description_text_id],
            children=tuple(child_values),
            field_hashes=tuple(field_hash_by_id[row[1]] for row in field_rows),
        )
        if _content_hash(canonical) != stored_hash:
            raise ValueError(f"node template {template_id} has an invalid content_hash")
        active_templates.remove(template_id)
        verified_template_hashes[template_id] = stored_hash
        return stored_hash

    for template_id in templates:
        verify_template(template_id)

    occurrences = {
        row[0]: row[1:]
        for row in connection.execute(
            """
            SELECT id, parent_id, template_id, sort_order, name_text_id,
                   start_addr, end_addr
            FROM node_occurrences ORDER BY id
            """
        )
    }
    occurrence_children: dict[int | None, list[int]] = {}
    for occurrence_id, values in occurrences.items():
        occurrence_children.setdefault(values[0], []).append(occurrence_id)
    reached = set()

    def verify_occurrence(occurrence_id: int) -> None:
        if occurrence_id in reached:
            raise ValueError("node occurrence graph contains a cycle or shared child")
        reached.add(occurrence_id)
        parent_id, template_id, _, _, start_blob, end_blob = occurrences[occurrence_id]
        start = decode_uint64(start_blob)
        end = decode_uint64(end_blob)
        size = decode_uint64(templates[template_id][2])
        if size == 0 or end != start + size - 1:
            raise ValueError(f"node occurrence {occurrence_id} has an invalid range")
        child_ids = occurrence_children.get(occurrence_id, [])
        child_ids.sort(key=lambda item: (occurrences[item][2], item))
        template_children = children_by_template.get(template_id, [])
        if len(child_ids) != len(template_children):
            raise ValueError(
                f"node occurrence {occurrence_id} does not instantiate its template"
            )
        for child_id, template_child in zip(child_ids, template_children):
            child_values = occurrences[child_id]
            child_parent_id, child_template_id, child_order, child_name_text_id, child_start_blob, _ = child_values
            edge_order, edge_template_id, relative_blob, edge_name_text_id = template_child
            if (
                child_parent_id != occurrence_id
                or child_order != edge_order
                or child_template_id != edge_template_id
                or child_name_text_id != edge_name_text_id
                or decode_uint64(child_start_blob) - start != decode_uint64(relative_blob)
            ):
                raise ValueError(
                    f"node occurrence {child_id} differs from parent template placement"
                )
            verify_occurrence(child_id)

    root_ids = occurrence_children.get(None, [])
    root_ids.sort(key=lambda item: (occurrences[item][2], item))
    if [occurrences[item][2] for item in root_ids] != list(range(root_count)):
        raise ValueError("root occurrence order is not contiguous")
    for root_id in root_ids:
        verify_occurrence(root_id)
    if len(reached) != node_count:
        raise ValueError("node occurrence graph contains unreachable nodes")

    return metadata, root_count, node_count, field_count


def validate_sqlite_report(database_path) -> SQLiteReportInfo:
    """Fully validate an existing report and return its verified metadata."""

    path = Path(database_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"SQLite report does not exist: {path}")
    connection = sqlite3.connect(str(path))
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA query_only = ON")
        schema_version = connection.execute("PRAGMA user_version").fetchone()[0]
        if schema_version == SCHEMA_VERSION_V1:
            metadata, root_count, node_count, field_count = _validate_v1_connection(
                connection
            )
        elif schema_version == SCHEMA_VERSION_V2:
            metadata, root_count, node_count, field_count = _validate_v2_connection(
                connection
            )
        else:
            raise ValueError(f"unsupported SQLite schema version: {schema_version}")
    finally:
        connection.close()
    return SQLiteReportInfo(
        path=path,
        database_bytes=path.stat().st_size,
        sha256=_file_sha256(path),
        root_count=root_count,
        node_count=node_count,
        field_count=field_count,
        metadata=metadata,
    )


def _write_sqlite_report_v1(roots, database_path, model_name=None) -> SQLiteReportInfo:
    """Atomically write and validate a normalized SQLite address-map report.

    ``roots`` is either one :class:`AddressSpace` or an ordered sequence of
    roots.  IDs are assigned by address-sorted pre-order traversal.  The target
    is replaced only after all schema and integrity checks pass.
    """

    root_nodes = _normalise_roots(roots)
    if model_name is None:
        model_name = (
            root_nodes[0].module_name if len(root_nodes) == 1 else "address_map"
        )
    model_name = _text(model_name, "model_name")

    target = Path(database_path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary_file = tempfile.NamedTemporaryFile(
        prefix=f".{target.name}.", suffix=".tmp", dir=str(target.parent), delete=False
    )
    temporary_path = Path(temporary_file.name)
    temporary_file.close()

    try:
        connection = sqlite3.connect(str(temporary_path))
        try:
            _configure_build_connection(connection, SCHEMA_VERSION_V1)
            connection.executescript(V1_TABLE_SCHEMA_SQL)
            connection.execute("BEGIN IMMEDIATE")
            writer = _V1ModelWriter(connection)
            for root_order, root in enumerate(root_nodes):
                writer.write_node(root, None, root_order)
            connection.executemany(
                "INSERT INTO metadata(key, value) VALUES (?, ?)",
                _v1_metadata_rows(
                    model_name=model_name,
                    root_count=len(root_nodes),
                    node_count=writer.node_count,
                    field_count=writer.field_count,
                ),
            )
            connection.commit()
            connection.executescript(V1_INDEX_SCHEMA_SQL)
            connection.commit()
            _validate_v1_connection(connection)
            connection.execute("VACUUM")
            _validate_v1_connection(connection)
        finally:
            connection.close()

        os.chmod(temporary_path, _publication_mode(target))
        os.replace(temporary_path, target)
    except BaseException:
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass
        raise

    return validate_sqlite_report(target)


def _v2_metadata_rows(*, model_name: str, model: _V2Model) -> tuple[tuple[str, str], ...]:
    logical_text_reference_count = 2 * (model.node_count + model.field_count)
    return (
        ("schema_version", str(SCHEMA_VERSION_V2)),
        ("generator_version", GENERATOR_VERSION_V2),
        ("viewer_min_version", VIEWER_MIN_VERSION_BY_SCHEMA[SCHEMA_VERSION_V2]),
        ("model_name", model_name),
        ("root_count", str(model.root_count)),
        ("node_count", str(model.node_count)),
        ("field_count", str(model.field_count)),
        ("node_template_count", str(len(model.node_templates))),
        (
            "node_template_reuse_count",
            str(model.node_count - len(model.node_templates)),
        ),
        ("field_definition_count", str(len(model.field_definitions))),
        (
            "field_definition_reuse_count",
            str(model.field_count - len(model.field_definitions)),
        ),
        ("text_count", str(len(model.texts))),
        ("text_reference_count", str(model.text_reference_count)),
        ("logical_text_reference_count", str(logical_text_reference_count)),
        ("text_reuse_count", str(logical_text_reference_count - len(model.texts))),
        ("text_utf8_bytes", str(model.text_utf8_bytes)),
        ("logical_text_utf8_bytes", str(model.logical_text_utf8_bytes)),
        (
            "text_utf8_saved_bytes",
            str(model.logical_text_utf8_bytes - model.text_utf8_bytes),
        ),
        ("template_child_count", str(model.template_child_count)),
        ("template_field_count", str(model.template_field_count)),
        ("access_enum", ACCESS_ENUM_JSON),
        ("access_value_enum", ACCESS_VALUE_ENUM_JSON),
    )


def _write_sqlite_report_v2(roots, database_path, model_name=None) -> SQLiteReportInfo:
    root_nodes = _normalise_roots(roots)
    if model_name is None:
        model_name = (
            root_nodes[0].module_name if len(root_nodes) == 1 else "address_map"
        )
    model_name = _text(model_name, "model_name")
    model = _V2Model.build(root_nodes)

    # Surrogate IDs are assigned from stable content, never discovery order or
    # Python identity. This also makes report bytes deterministic after VACUUM.
    text_ids = {
        value: index
        for index, value in enumerate(
            sorted(model.texts, key=lambda value: value.encode("utf-8")), start=1
        )
    }
    field_ids = {
        content_hash: index
        for index, content_hash in enumerate(sorted(model.field_definitions), start=1)
    }
    template_ids = {
        content_hash: index
        for index, content_hash in enumerate(sorted(model.node_templates), start=1)
    }

    target = Path(database_path).expanduser().resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary_file = tempfile.NamedTemporaryFile(
        prefix=f".{target.name}.", suffix=".tmp", dir=str(target.parent), delete=False
    )
    temporary_path = Path(temporary_file.name)
    temporary_file.close()

    try:
        connection = sqlite3.connect(str(temporary_path))
        try:
            _configure_build_connection(connection, SCHEMA_VERSION_V2)
            connection.executescript(V2_TABLE_SCHEMA_SQL)
            connection.execute("BEGIN IMMEDIATE")
            connection.executemany(
                "INSERT INTO texts(id, value) VALUES (?, ?)",
                ((text_id, value) for value, text_id in text_ids.items()),
            )

            connection.executemany(
                """
                INSERT INTO field_defs(
                    id, content_hash, name_text_id, lsb, msb, external,
                    sw_access, hw_access, default_value, description_text_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    (
                        field_ids[content_hash],
                        definition.content_hash,
                        text_ids[definition.name],
                        definition.lsb,
                        definition.msb,
                        definition.external,
                        definition.sw_access,
                        definition.hw_access,
                        definition.default_value,
                        text_ids[definition.description],
                    )
                    for content_hash, definition in sorted(
                        model.field_definitions.items()
                    )
                ),
            )
            connection.executemany(
                """
                INSERT INTO node_templates(
                    id, content_hash, kind, size_bytes, description_text_id,
                    child_count, field_count
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    (
                        template_ids[content_hash],
                        template.content_hash,
                        template.kind,
                        encode_uint64(template.size_bytes),
                        text_ids[template.description],
                        len(template.children),
                        len(template.field_hashes),
                    )
                    for content_hash, template in sorted(model.node_templates.items())
                ),
            )
            connection.executemany(
                """
                INSERT INTO template_children(
                    parent_template_id, sort_order, child_template_id,
                    relative_addr, child_name_text_id
                ) VALUES (?, ?, ?, ?, ?)
                """,
                (
                    (
                        template_ids[content_hash],
                        child.sort_order,
                        template_ids[child.child_hash],
                        encode_uint64(child.relative_addr),
                        text_ids[child.child_name],
                    )
                    for content_hash, template in sorted(model.node_templates.items())
                    for child in template.children
                ),
            )
            connection.executemany(
                """
                INSERT INTO template_fields(
                    register_template_id, sort_order, field_def_id
                ) VALUES (?, ?, ?)
                """,
                (
                    (
                        template_ids[content_hash],
                        sort_order,
                        field_ids[field_hash],
                    )
                    for content_hash, template in sorted(model.node_templates.items())
                    for sort_order, field_hash in enumerate(template.field_hashes)
                ),
            )
            connection.executemany(
                """
                INSERT INTO node_occurrences(
                    id, parent_id, template_id, sort_order, name_text_id,
                    start_addr, end_addr
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    (
                        occurrence.id,
                        occurrence.parent_id,
                        template_ids[occurrence.template_hash],
                        occurrence.sort_order,
                        text_ids[occurrence.name],
                        encode_uint64(occurrence.start_addr),
                        encode_uint64(occurrence.end_addr),
                    )
                    for occurrence in model.occurrences
                ),
            )
            connection.executemany(
                "INSERT INTO metadata(key, value) VALUES (?, ?)",
                _v2_metadata_rows(model_name=model_name, model=model),
            )
            connection.commit()
            connection.executescript(V2_INDEX_SCHEMA_SQL)
            connection.commit()
            _validate_v2_connection(connection)
            connection.execute("VACUUM")
            _validate_v2_connection(connection)
        finally:
            connection.close()

        os.chmod(temporary_path, _publication_mode(target))
        os.replace(temporary_path, target)
    except BaseException:
        try:
            temporary_path.unlink()
        except FileNotFoundError:
            pass
        raise
    return validate_sqlite_report(target)


def write_sqlite_report(
    roots,
    database_path,
    model_name=None,
    *,
    schema_version: int = SCHEMA_VERSION,
) -> SQLiteReportInfo:
    """Atomically write an address-map report in schema v2 or legacy v1.

    v2 is the default and stores logical occurrences separately from shared,
    content-addressed templates. Pass ``schema_version=SCHEMA_VERSION_V1`` for
    a byte-stable legacy report during migration.
    """

    if not isinstance(schema_version, int) or isinstance(schema_version, bool):
        raise TypeError("schema_version must be an integer")
    if schema_version == SCHEMA_VERSION_V1:
        return _write_sqlite_report_v1(roots, database_path, model_name)
    if schema_version == SCHEMA_VERSION_V2:
        return _write_sqlite_report_v2(roots, database_path, model_name)
    raise ValueError(
        f"unsupported schema_version {schema_version!r}; "
        f"expected one of {SUPPORTED_SCHEMA_VERSIONS!r}"
    )


__all__ = [
    "ACCESS_ENUM_JSON",
    "ACCESS_VALUE_ENUM_JSON",
    "FIELD_ACCESS_CODE_BY_NAME",
    "FIELD_ACCESS_MEMBERS",
    "FIELD_ACCESS_NAMES",
    "FIELD_ACCESS_NAME_BY_CODE",
    "FIELD_ACCESS_TO_CODE",
    "FIELD_ACCESS_VALUE_BY_CODE",
    "GENERATOR_VERSION",
    "GENERATOR_VERSION_V1",
    "GENERATOR_VERSION_V2",
    "NODE_KIND_ADDRESS_SPACE",
    "NODE_KIND_MEMORY",
    "NODE_KIND_NAMES",
    "NODE_KIND_REGISTER",
    "NODE_KIND_REG_SPACE",
    "SCHEMA_VERSION",
    "SCHEMA_VERSION_V1",
    "SCHEMA_VERSION_V2",
    "SUPPORTED_SCHEMA_VERSIONS",
    "SQLITE_APPLICATION_ID",
    "SQLiteReportInfo",
    "UINT64_MAX",
    "VIEWER_MIN_VERSION",
    "VIEWER_MIN_VERSION_BY_SCHEMA",
    "decode_uint64",
    "encode_uint64",
    "encode_uint_minimal",
    "validate_sqlite_report",
    "write_sqlite_report",
]
