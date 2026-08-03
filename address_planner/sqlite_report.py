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


SCHEMA_VERSION = 1
GENERATOR_VERSION = "address_planner.sqlite_report/1"
VIEWER_MIN_VERSION = "1"
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


TABLE_SCHEMA_SQL = f"""
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

INDEX_SCHEMA_SQL = """
CREATE INDEX idx_nodes_parent_order
ON nodes(parent_id, sort_order, id);

CREATE INDEX idx_nodes_parent_address
ON nodes(parent_id, start_addr, id);

CREATE INDEX idx_nodes_name
ON nodes(name);

CREATE INDEX idx_fields_register_order
ON fields(register_id, sort_order, id);
"""

REQUIRED_TABLES = frozenset(("metadata", "nodes", "fields", "node_attributes"))
REQUIRED_INDEXES = frozenset(
    (
        "idx_nodes_parent_order",
        "idx_nodes_parent_address",
        "idx_nodes_name",
        "idx_fields_register_order",
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


class _ModelWriter:
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


def _metadata_rows(
    *, model_name: str, root_count: int, node_count: int, field_count: int
) -> tuple[tuple[str, str], ...]:
    return (
        ("schema_version", str(SCHEMA_VERSION)),
        ("generator_version", GENERATOR_VERSION),
        ("viewer_min_version", VIEWER_MIN_VERSION),
        ("model_name", model_name),
        ("root_count", str(root_count)),
        ("node_count", str(node_count)),
        ("field_count", str(field_count)),
        ("access_enum", ACCESS_ENUM_JSON),
        ("access_value_enum", ACCESS_VALUE_ENUM_JSON),
    )


def _configure_build_connection(connection: sqlite3.Connection) -> None:
    connection.execute("PRAGMA journal_mode = OFF")
    connection.execute("PRAGMA synchronous = OFF")
    connection.execute("PRAGMA temp_store = MEMORY")
    connection.execute("PRAGMA foreign_keys = ON")
    connection.execute(f"PRAGMA application_id = {SQLITE_APPLICATION_ID}")
    connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")


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


def _validate_connection(
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
    if user_version != SCHEMA_VERSION:
        raise ValueError(f"unexpected SQLite user_version: {user_version}")

    objects = dict(
        connection.execute(
            "SELECT name, type FROM sqlite_master WHERE type IN ('table', 'index')"
        )
    )
    missing_tables = REQUIRED_TABLES.difference(objects)
    missing_indexes = REQUIRED_INDEXES.difference(objects)
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
    if metadata["schema_version"] != str(SCHEMA_VERSION):
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


def validate_sqlite_report(database_path) -> SQLiteReportInfo:
    """Fully validate an existing report and return its verified metadata."""

    path = Path(database_path).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"SQLite report does not exist: {path}")
    connection = sqlite3.connect(str(path))
    try:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA query_only = ON")
        metadata, root_count, node_count, field_count = _validate_connection(connection)
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


def write_sqlite_report(roots, database_path, model_name=None) -> SQLiteReportInfo:
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
            _configure_build_connection(connection)
            connection.executescript(TABLE_SCHEMA_SQL)
            connection.execute("BEGIN IMMEDIATE")
            writer = _ModelWriter(connection)
            for root_order, root in enumerate(root_nodes):
                writer.write_node(root, None, root_order)
            connection.executemany(
                "INSERT INTO metadata(key, value) VALUES (?, ?)",
                _metadata_rows(
                    model_name=model_name,
                    root_count=len(root_nodes),
                    node_count=writer.node_count,
                    field_count=writer.field_count,
                ),
            )
            connection.commit()
            connection.executescript(INDEX_SCHEMA_SQL)
            connection.commit()
            _validate_connection(connection)
            connection.execute("VACUUM")
            _validate_connection(connection)
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
    "NODE_KIND_ADDRESS_SPACE",
    "NODE_KIND_MEMORY",
    "NODE_KIND_NAMES",
    "NODE_KIND_REGISTER",
    "NODE_KIND_REG_SPACE",
    "SCHEMA_VERSION",
    "SQLITE_APPLICATION_ID",
    "SQLiteReportInfo",
    "UINT64_MAX",
    "VIEWER_MIN_VERSION",
    "decode_uint64",
    "encode_uint64",
    "encode_uint_minimal",
    "validate_sqlite_report",
    "write_sqlite_report",
]
