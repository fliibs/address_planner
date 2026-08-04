import base64
import gzip
import json
import stat
import sqlite3

import pytest

from address_planner import (
    ACCESS_ENUM_JSON,
    ACCESS_VALUE_ENUM_JSON,
    FIELD_ACCESS_CODE_BY_NAME,
    FIELD_ACCESS_MEMBERS,
    FIELD_ACCESS_NAMES,
    FIELD_ACCESS_NAME_BY_CODE,
    FIELD_ACCESS_TO_CODE,
    FIELD_ACCESS_VALUE_BY_CODE,
    NODE_KIND_ADDRESS_SPACE,
    NODE_KIND_REGISTER,
    NODE_KIND_REG_SPACE,
    Options,
    DATABASE_PLACEHOLDER,
    MANIFEST_PLACEHOLDER,
    AddressSpace,
    ExternalField,
    Field,
    FieldAccess,
    ReadOnly,
    ReadWrite,
    RegSpace,
    Register,
    SCHEMA_VERSION,
    SCHEMA_VERSION_V1,
    SCHEMA_VERSION_V2,
    UINT64_MAX,
    decode_uint64,
    encode_uint64,
    validate_sqlite_report,
    package_single_html,
    write_sqlite_report,
)


def _fixture_model():
    top = AddressSpace("top", 4096, "top description")

    late = RegSpace("late_bank", 512, "later in address order")
    early = RegSpace("early_bank", 512, "earlier in address order")
    control = Register("control", bit=64, description="control register")
    control.add(
        ExternalField(
            "wide",
            bit=61,
            sw_access=ReadWrite,
            hw_access=ReadOnly,
            init_value=(1 << 60) + 3,
            description="larger than a JavaScript safe integer",
        ),
        offset=0,
    )
    control.add(Field("flag", bit=1, sw_access=ReadOnly, hw_access=ReadWrite), 63)
    early.add(control, offset=32)

    # Insert in reverse address order.  The report must use the established
    # address-sorted model order, not insertion order.
    top.add(late, offset=2048)
    top.add(early, offset=0)
    return top


def _connect(path):
    connection = sqlite3.connect(str(path))
    connection.row_factory = sqlite3.Row
    return connection


def _logical_projection(path):
    """Return exactly the Viewer-visible Node/Field semantics for either schema."""

    with _connect(path) as connection:
        schema_version = connection.execute("PRAGMA user_version").fetchone()[0]
        if schema_version == SCHEMA_VERSION_V1:
            nodes = [
                (
                    row["id"], row["parent_id"], row["kind"], row["sort_order"],
                    row["name"], decode_uint64(row["start_addr"]),
                    decode_uint64(row["end_addr"]), decode_uint64(row["size_bytes"]),
                    row["description"], row["child_count"], row["field_count"],
                )
                for row in connection.execute("SELECT * FROM nodes ORDER BY id")
            ]
            fields = [
                (
                    row["register_id"], row["sort_order"], row["name"],
                    row["lsb"], row["msb"], row["external"], row["sw_access"],
                    row["hw_access"], row["default_value"], row["description"],
                )
                for row in connection.execute("SELECT * FROM fields ORDER BY id")
            ]
        elif schema_version == SCHEMA_VERSION_V2:
            nodes = [
                (
                    row["id"], row["parent_id"], row["kind"], row["sort_order"],
                    row["name"], decode_uint64(row["start_addr"]),
                    decode_uint64(row["end_addr"]), decode_uint64(row["size_bytes"]),
                    row["description"], row["child_count"], row["field_count"],
                )
                for row in connection.execute(
                    """
                    SELECT occurrence.id, occurrence.parent_id, template.kind,
                           occurrence.sort_order, name.value AS name,
                           occurrence.start_addr, occurrence.end_addr,
                           template.size_bytes, description.value AS description,
                           template.child_count, template.field_count
                    FROM node_occurrences AS occurrence
                    JOIN node_templates AS template
                      ON template.id = occurrence.template_id
                    JOIN texts AS name ON name.id = occurrence.name_text_id
                    JOIN texts AS description
                      ON description.id = template.description_text_id
                    ORDER BY occurrence.id
                    """
                )
            ]
            fields = [
                (
                    row["register_id"], row["sort_order"], row["name"],
                    row["lsb"], row["msb"], row["external"], row["sw_access"],
                    row["hw_access"], row["default_value"], row["description"],
                )
                for row in connection.execute(
                    """
                    SELECT occurrence.id AS register_id,
                           layout.sort_order, name.value AS name,
                           field.lsb, field.msb, field.external,
                           field.sw_access, field.hw_access, field.default_value,
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
            ]
        else:
            raise AssertionError(f"unexpected schema {schema_version}")
    return nodes, fields


def test_field_access_contract_is_complete_stable_and_embedded(tmp_path):
    assert len(FIELD_ACCESS_MEMBERS) == 28
    assert tuple(FieldAccess) == FIELD_ACCESS_MEMBERS
    assert tuple(member.name for member in FieldAccess) == FIELD_ACCESS_NAMES
    assert [FIELD_ACCESS_TO_CODE[member] for member in FieldAccess] == list(range(28))
    assert FIELD_ACCESS_CODE_BY_NAME == {
        member.name: code for code, member in enumerate(FieldAccess)
    }
    assert FIELD_ACCESS_NAME_BY_CODE == {
        code: member.name for code, member in enumerate(FieldAccess)
    }
    assert FIELD_ACCESS_VALUE_BY_CODE == {
        code: member.value for code, member in enumerate(FieldAccess)
    }

    report = write_sqlite_report(_fixture_model(), tmp_path / "map.sqlite")
    assert json.loads(report.metadata["access_enum"]) == {
        str(code): member.name for code, member in enumerate(FieldAccess)
    }
    assert json.loads(report.metadata["access_value_enum"]) == {
        str(code): member.value for code, member in enumerate(FieldAccess)
    }
    assert report.metadata["access_enum"] == ACCESS_ENUM_JSON
    assert report.metadata["access_value_enum"] == ACCESS_VALUE_ENUM_JSON


def test_normalized_schema_addresses_fields_and_lazy_query_shape(tmp_path):
    report = write_sqlite_report(
        _fixture_model(), tmp_path / "map.sqlite", schema_version=SCHEMA_VERSION_V1
    )
    assert report.root_count == 1
    assert report.node_count == 4
    assert report.field_count == 2
    assert report.sha256 == validate_sqlite_report(report.path).sha256

    with _connect(report.path) as connection:
        objects = {
            row["name"]: row["type"]
            for row in connection.execute(
                "SELECT name, type FROM sqlite_master "
                "WHERE name NOT LIKE 'sqlite_%'"
            )
        }
        assert objects["nodes"] == "table"
        assert objects["fields"] == "table"
        assert objects["metadata"] == "table"
        assert objects["node_attributes"] == "table"
        assert objects["idx_nodes_parent_order"] == "index"
        assert objects["idx_fields_register_order"] == "index"

        nodes = list(
            connection.execute(
                "SELECT * FROM nodes ORDER BY id"
            )
        )
        assert [(row["id"], row["parent_id"], row["kind"], row["sort_order"], row["name"])
                for row in nodes] == [
            (1, None, NODE_KIND_ADDRESS_SPACE, 0, "top"),
            (2, 1, NODE_KIND_REG_SPACE, 0, "early_bank"),
            (3, 2, NODE_KIND_REGISTER, 0, "control"),
            (4, 1, NODE_KIND_REG_SPACE, 1, "late_bank"),
        ]
        assert [
            (decode_uint64(row["start_addr"]), decode_uint64(row["end_addr"]),
             decode_uint64(row["size_bytes"]))
            for row in nodes
        ] == [
            (0, 4095, 4096),
            (0, 511, 512),
            (32, 39, 8),
            (2048, 2559, 512),
        ]

        # These are the exact bounded query shapes the Viewer uses: roots,
        # direct children, then fields only for the selected register.
        roots = list(connection.execute(
            "SELECT name FROM nodes WHERE parent_id IS NULL ORDER BY sort_order, id LIMIT 200"
        ))
        children = list(connection.execute(
            "SELECT name FROM nodes WHERE parent_id = ? ORDER BY sort_order, id LIMIT 200",
            (1,),
        ))
        fields = list(connection.execute(
            "SELECT * FROM fields WHERE register_id = ? ORDER BY sort_order, id LIMIT 200",
            (3,),
        ))
        assert [row["name"] for row in roots] == ["top"]
        assert [row["name"] for row in children] == ["early_bank", "late_bank"]
        assert [row["name"] for row in fields] == ["wide", "flag"]
        assert int.from_bytes(fields[0]["default_value"], "big") == (1 << 60) + 3
        assert fields[0]["external"] == 1
        assert fields[0]["sw_access"] == FIELD_ACCESS_TO_CODE[ReadWrite]
        assert fields[0]["hw_access"] == FIELD_ACCESS_TO_CODE[ReadOnly]

        assert connection.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
        assert list(connection.execute("PRAGMA foreign_key_check")) == []


def test_ids_order_and_database_bytes_are_deterministic(tmp_path):
    first = write_sqlite_report(_fixture_model(), tmp_path / "first.sqlite")
    second = write_sqlite_report(_fixture_model(), tmp_path / "second.sqlite")
    assert first.sha256 == second.sha256
    assert first.path.read_bytes() == second.path.read_bytes()
    legacy_first = write_sqlite_report(
        _fixture_model(), tmp_path / "legacy-first.sqlite",
        schema_version=SCHEMA_VERSION_V1,
    )
    legacy_second = write_sqlite_report(
        _fixture_model(), tmp_path / "legacy-second.sqlite",
        schema_version=SCHEMA_VERSION_V1,
    )
    assert legacy_first.path.read_bytes() == legacy_second.path.read_bytes()


def test_schema_v2_is_default_and_v1_remains_an_explicit_option(tmp_path):
    assert SCHEMA_VERSION == SCHEMA_VERSION_V2
    default_report = _fixture_model().report_sqlite(tmp_path / "default.sqlite")
    legacy_report = _fixture_model().report_sqlite(
        tmp_path / "legacy.sqlite", schema_version=SCHEMA_VERSION_V1
    )
    assert default_report.metadata["schema_version"] == "2"
    assert legacy_report.metadata["schema_version"] == "1"
    with _connect(default_report.path) as connection:
        objects = {
            row[0]: row[1]
            for row in connection.execute(
                "SELECT name, type FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'"
            )
        }
    assert objects["node_occurrences"] == "table"
    assert objects["node_templates"] == "table"
    assert objects["idx_occurrences_parent_order"] == "index"
    assert objects["idx_occurrences_address"] == "index"
    assert "node_attributes" not in objects
    with pytest.raises(ValueError, match="unsupported schema_version"):
        write_sqlite_report(_fixture_model(), tmp_path / "v3.sqlite", schema_version=3)


def test_schema_v1_and_v2_have_identical_visible_semantics(tmp_path):
    model = _fixture_model()
    v1 = write_sqlite_report(
        model, tmp_path / "v1.sqlite", schema_version=SCHEMA_VERSION_V1
    )
    v2 = write_sqlite_report(
        model, tmp_path / "v2.sqlite", schema_version=SCHEMA_VERSION_V2
    )
    assert _logical_projection(v1.path) == _logical_projection(v2.path)


def _reused_bank_model():
    register = Register("template", bit=32, description="same register")
    register.add(
        Field("enable", bit=1, sw_access=ReadWrite, hw_access=ReadOnly), 0
    )
    register.add(
        Field(
            "mode", bit=2, sw_access=ReadOnly, hw_access=ReadWrite,
            init_value=2, description="same field description",
        ),
        4,
    )
    bank = RegSpace("bank_template", 8, "same bank")
    bank.add(register, 0, "control")
    bank.add(register, 4, "status")
    top = AddressSpace("top", 8192, "root")
    top.add(bank, 0, "bank_a")
    top.add(bank, 4096, "bank_b")
    return top


def test_deepcopied_banks_share_templates_but_keep_absolute_occurrences(tmp_path):
    report = write_sqlite_report(_reused_bank_model(), tmp_path / "reuse.sqlite")
    assert report.node_count == 7
    assert report.field_count == 8
    assert report.metadata["node_template_count"] == "3"
    assert report.metadata["node_template_reuse_count"] == "4"
    assert report.metadata["field_definition_count"] == "2"
    assert report.metadata["field_definition_reuse_count"] == "6"
    assert report.reuse_statistics["node_template_reuse_count"] == 4
    assert report.schema_version == SCHEMA_VERSION_V2
    assert int(report.metadata["text_count"]) < int(
        report.metadata["logical_text_reference_count"]
    )

    with _connect(report.path) as connection:
        banks = list(
            connection.execute(
                """
                SELECT occurrence.template_id, occurrence.start_addr
                FROM node_occurrences AS occurrence
                JOIN node_templates AS template
                  ON template.id = occurrence.template_id
                WHERE template.kind = ? ORDER BY occurrence.id
                """,
                (NODE_KIND_REG_SPACE,),
            )
        )
        registers = list(
            connection.execute(
                """
                SELECT occurrence.template_id, occurrence.start_addr
                FROM node_occurrences AS occurrence
                JOIN node_templates AS template
                  ON template.id = occurrence.template_id
                WHERE template.kind = ? ORDER BY occurrence.id
                """,
                (NODE_KIND_REGISTER,),
            )
        )
    assert len({row["template_id"] for row in banks}) == 1
    assert len({row["template_id"] for row in registers}) == 1
    assert [decode_uint64(row["start_addr"]) for row in registers] == [
        0, 4, 4096, 4100,
    ]


def test_one_byte_semantic_difference_does_not_merge_field_or_parent_templates(
    tmp_path,
):
    def bank_with_reset(reset):
        register = Register("control", bit=32, description="register")
        register.add(
            Field(
                "enable", bit=1, sw_access=ReadWrite, hw_access=ReadOnly,
                init_value=reset, description="field",
            ),
            0,
        )
        bank = RegSpace("bank", 4, "bank")
        bank.add(register, 0)
        return bank

    top = AddressSpace("top", 8192)
    top.add(bank_with_reset(0), 0, "bank_a")
    top.add(bank_with_reset(1), 4096, "bank_b")
    report = write_sqlite_report(top, tmp_path / "different.sqlite")
    assert report.metadata["field_definition_count"] == "2"
    with _connect(report.path) as connection:
        hashes_by_kind = {
            kind: count
            for kind, count in connection.execute(
                """
                SELECT kind, count(DISTINCT content_hash)
                FROM node_templates GROUP BY kind
                """
            )
        }
    assert hashes_by_kind[NODE_KIND_REGISTER] == 2
    assert hashes_by_kind[NODE_KIND_REG_SPACE] == 2


def test_hash_collision_never_merges_distinct_canonical_semantics(tmp_path, monkeypatch):
    import address_planner.sqlite_report as sqlite_report_module

    model = _reused_bank_model()
    monkeypatch.setattr(sqlite_report_module, "_content_hash", lambda _: b"x" * 32)
    with pytest.raises(ValueError, match="collision"):
        write_sqlite_report(model, tmp_path / "collision.sqlite")


def test_v2_occurrences_preserve_address_sorted_preorder(tmp_path):
    report = write_sqlite_report(_fixture_model(), tmp_path / "ordered.sqlite")
    with _connect(report.path) as connection:
        rows = list(
            connection.execute(
                """
                SELECT occurrence.id, occurrence.parent_id,
                       occurrence.sort_order, name.value AS name,
                       occurrence.start_addr
                FROM node_occurrences AS occurrence
                JOIN texts AS name ON name.id = occurrence.name_text_id
                ORDER BY occurrence.id
                """
            )
        )
    assert [(row["id"], row["parent_id"], row["sort_order"], row["name"])
            for row in rows] == [
        (1, None, 0, "top"),
        (2, 1, 0, "early_bank"),
        (3, 2, 0, "control"),
        (4, 1, 1, "late_bank"),
    ]
    assert [decode_uint64(row["start_addr"]) for row in rows] == [0, 0, 32, 2048]


def test_v2_multiport_same_address_preserves_insertion_order(tmp_path):
    register = Register("view", bit=32)
    register.add(Field("value", bit=1), 0)
    bank = RegSpace("bank", 4)
    previous = Options.MultiPortOption
    Options.MultiPortOption = True
    try:
        bank.add(register, 0, "view_b")
        bank.add(register, 0, "view_a")
    finally:
        Options.MultiPortOption = previous
    top = AddressSpace("top", 4)
    top.add(bank, 0)

    report = write_sqlite_report(top, tmp_path / "multiport.sqlite")
    with _connect(report.path) as connection:
        rows = list(
            connection.execute(
                """
                SELECT occurrence.sort_order, name.value, occurrence.start_addr
                FROM node_occurrences AS occurrence
                JOIN node_templates AS template
                  ON template.id = occurrence.template_id
                JOIN texts AS name ON name.id = occurrence.name_text_id
                WHERE template.kind = ? ORDER BY occurrence.sort_order
                """,
                (NODE_KIND_REGISTER,),
            )
        )
    assert [(row["sort_order"], row["value"]) for row in rows] == [
        (0, "view_b"),
        (1, "view_a"),
    ]
    assert [decode_uint64(row["start_addr"]) for row in rows] == [0, 0]


def test_uint64_boundary_and_large_field_default(tmp_path):
    class HighAddressSpace(AddressSpace):
        @property
        def global_start_address(self):
            return UINT64_MAX * 8

    model = HighAddressSpace("last_byte", 1)
    report = write_sqlite_report(model, tmp_path / "max.sqlite")
    with _connect(report.path) as connection:
        row = connection.execute(
            """
            SELECT occurrence.start_addr, occurrence.end_addr, template.size_bytes
            FROM node_occurrences AS occurrence
            JOIN node_templates AS template
              ON template.id = occurrence.template_id
            """
        ).fetchone()
    assert decode_uint64(row["start_addr"]) == UINT64_MAX
    assert decode_uint64(row["end_addr"]) == UINT64_MAX
    assert decode_uint64(row["size_bytes"]) == 1
    assert encode_uint64(UINT64_MAX) == b"\xff" * 8
    with pytest.raises(ValueError, match="out of range"):
        encode_uint64(UINT64_MAX + 1)


def test_failed_generation_does_not_replace_existing_target(tmp_path):
    class OutOfRangeAddressSpace(AddressSpace):
        @property
        def global_start_address(self):
            return UINT64_MAX * 8

    target = tmp_path / "preserved.sqlite"
    target.write_bytes(b"keep me")
    with pytest.raises(ValueError, match="out of range"):
        write_sqlite_report(OutOfRangeAddressSpace("overflow", 2), target)
    assert target.read_bytes() == b"keep me"


def test_address_space_convenience_api_keeps_json_available(tmp_path):
    model = _fixture_model()
    sqlite_info = model.report_sqlite(tmp_path / "report.sqlite")
    assert sqlite_info.path.is_file()

    model.path = str(tmp_path)
    model.report_json()
    assert model.json_path.endswith("data.json")
    with open(model.json_path, encoding="utf-8") as handle:
        json_report = json.load(handle)
    assert json_report[0]["name"] == "top"
    assert json_report[0]["children"][0]["name"] == "early_bank"
    assert json_report[0]["children"][0]["children"][0]["name"] == "control"


def _viewer_template(tmp_path):
    template = tmp_path / "viewer.template.html"
    template.write_text(
        "<!doctype html><script id='apv-manifest' type='application/json'>"
        f"{MANIFEST_PLACEHOLDER}</script>"
        "<script id='apv-database' type='application/octet-stream'>"
        f"{DATABASE_PLACEHOLDER}</script><main>viewer</main>",
        encoding="utf-8",
    )
    return template


def test_single_html_packager_embeds_verified_gzip_database(tmp_path):
    database = write_sqlite_report(_fixture_model(), tmp_path / "map.sqlite")
    template = _viewer_template(tmp_path)
    output = tmp_path / "map.html"

    packaged = package_single_html(database.path, template, output)
    html = output.read_text(encoding="utf-8")
    assert packaged.path == output.resolve()
    assert packaged.database_bytes == database.database_bytes
    assert packaged.database_sha256 == database.sha256
    assert MANIFEST_PLACEHOLDER not in html
    assert DATABASE_PLACEHOLDER not in html

    manifest_text = html.split("type='application/json'>", 1)[1].split("</script>", 1)[0]
    manifest = json.loads(manifest_text)
    encoded = html.split("type='application/octet-stream'>", 1)[1].split("</script>", 1)[0]
    compressed = base64.b64decode(encoded, validate=True)
    assert len(compressed) == manifest["compressedBytes"]
    assert gzip.decompress(compressed) == database.path.read_bytes()
    assert manifest == packaged.manifest
    assert manifest["schemaVersion"] == SCHEMA_VERSION_V2
    assert stat.S_IMODE(output.stat().st_mode) == 0o644
    assert stat.S_IMODE(database.path.stat().st_mode) == 0o644


def test_atomic_replacement_preserves_existing_delivery_mode(tmp_path):
    database_path = tmp_path / "map.sqlite"
    database_path.write_bytes(b"old")
    database_path.chmod(0o640)
    database = write_sqlite_report(_fixture_model(), database_path)
    assert stat.S_IMODE(database.path.stat().st_mode) == 0o640

    output = tmp_path / "map.html"
    output.write_text("old", encoding="utf-8")
    output.chmod(0o640)
    package_single_html(database.path, _viewer_template(tmp_path), output)
    assert stat.S_IMODE(output.stat().st_mode) == 0o640


def test_generate_defaults_to_single_html_without_json(tmp_path):
    model = _fixture_model()
    template = _viewer_template(tmp_path)
    model.generate(str(tmp_path / "generated"), viewer_template_path=template)

    html_dir = tmp_path / "generated" / "top" / "html"
    assert not (html_dir / "data.json").exists()
    assert (html_dir / "top_address_map.html").is_file()
    assert not list(html_dir.glob("*.sqlite"))


def test_generate_can_explicitly_publish_json_and_single_html_together(tmp_path):
    model = _fixture_model()
    template = _viewer_template(tmp_path)
    model.generate(
        str(tmp_path / "generated"),
        viewer_template_path=template,
        report_json=True,
    )

    html_dir = tmp_path / "generated" / "top" / "html"
    assert (html_dir / "data.json").is_file()
    assert (html_dir / "top_address_map.html").is_file()


def test_generate_threads_explicit_legacy_schema_to_single_html(tmp_path):
    model = _fixture_model()
    template = _viewer_template(tmp_path)
    model.generate(
        str(tmp_path / "legacy-generated"),
        viewer_template_path=template,
        sqlite_schema_version=SCHEMA_VERSION_V1,
    )

    html_path = (
        tmp_path / "legacy-generated" / "top" / "html" / "top_address_map.html"
    )
    html = html_path.read_text(encoding="utf-8")
    manifest_text = html.split("type='application/json'>", 1)[1].split(
        "</script>", 1
    )[0]
    assert json.loads(manifest_text)["schemaVersion"] == SCHEMA_VERSION_V1
