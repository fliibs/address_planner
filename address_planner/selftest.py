"""Small runtime diagnostics for the documented address-planner setup path."""

from __future__ import annotations

import argparse
import hashlib
import importlib.metadata
import inspect
import json
import os
import platform
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path, PureWindowsPath
from typing import Any

from . import Component
from ._runtime import (
    LEGACY_UHDL_ROOT,
    RuntimeConfigurationError,
    load_canonical_uhdl,
    resolve_address_planner_root,
    resolve_uhdl_root,
)


_MODEL_SCHEMA_VERSION = 1
_REQUIRED_CLASSES = (
    "register_rtl",
    "c_header",
    "verilog_header",
    "ralf",
    "json",
)
_NAME_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")
_SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
_MANIFEST_KEYS = {
    "schema_version",
    "model",
    "runtime",
    "output_root",
    "artifacts",
    "auxiliary_artifacts",
    "verification_records",
}
_ARTIFACT_KEYS = {"class", "status", "path", "size_bytes", "sha256"}
_VERIFICATION_RECORD_KEYS = {"kind", "tool", "argv", "exit_code", "inputs", "log"}
_BEHAVIOR_VERIFICATION_RECORD_KEYS = _VERIFICATION_RECORD_KEYS | {"run", "supporting_artifacts"}
_VERIFICATION_TOOL_KEYS = {"requested", "path", "version"}
_VERIFICATION_INPUT_KEYS = {"model_sha256", "required_artifact_sha256"}
_VERIFICATION_LOG_KEYS = {"path", "size_bytes", "sha256"}
_VERIFICATION_RUN_KEYS = {"argv", "exit_code"}


class ModelValidationError(ValueError):
    """Raised when a programmatic register model is not in the fixed JSON schema."""


class ManifestValidationError(ValueError):
    """Raised when a delivery manifest cannot be trusted as an artifact inventory."""


def _revision(root: Path) -> str:
    try:
        return subprocess.check_output(
            ["git", "-C", str(root), "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unavailable"


def _version(distribution: str) -> str | None:
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None


def _tool(tool: str) -> dict[str, str | None]:
    executable = shutil.which(tool)
    version = None
    if executable:
        try:
            version = subprocess.check_output(
                [executable, "--version"], text=True, stderr=subprocess.STDOUT, timeout=5
            ).splitlines()[0]
        except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired):
            version = "unavailable"
    return {"path": executable, "version": version}


def _below(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def preflight(report: Path) -> dict[str, Any]:
    planner_root = resolve_address_planner_root()
    uhdl_root = resolve_uhdl_root()
    uhdl = load_canonical_uhdl()
    component_source = Path(inspect.getfile(Component)).resolve()
    if _below(component_source, LEGACY_UHDL_ROOT):
        raise RuntimeConfigurationError(
            f"Component resolved from forbidden legacy snapshot: {component_source}"
        )
    if not _below(component_source, uhdl_root):
        raise RuntimeConfigurationError(
            f"Component resolved outside canonical UHDL_ROOT: {component_source}"
        )

    payload: dict[str, Any] = {
        "schema_version": 1,
        "address_planner": {
            "root": str(planner_root),
            "module": str(Path(sys.modules["address_planner"].__file__).resolve()),
            "revision": _revision(planner_root),
        },
        "uhdl": {
            "root": str(uhdl_root),
            "revision": _revision(uhdl_root),
            "module": str(Path(uhdl.__file__).resolve()),
            "component": str(component_source),
            "component_is_below_legacy_snapshot": False,
        },
        "python": {
            "executable": sys.executable,
            "implementation": platform.python_implementation(),
            "version": platform.python_version(),
        },
        "dependencies": {
            name: _version(name)
            for name in ("Jinja2", "openpyxl", "networkx", "matplotlib", "pytest")
        },
        "tools": {name: _tool(name) for name in ("verilator", "iverilog", "vcs", "xrun", "vsim")},
    }
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(encoded, encoding="utf-8")
    payload["report_sha256"] = hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    return payload


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _expect_exact_keys(value: Any, keys: set[str], context: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ModelValidationError(f"{context} must be an object")
    actual = set(value)
    missing = sorted(keys - actual)
    unknown = sorted(actual - keys)
    if missing or unknown:
        parts = []
        if missing:
            parts.append(f"missing keys: {', '.join(missing)}")
        if unknown:
            parts.append(f"unknown keys: {', '.join(unknown)}")
        raise ModelValidationError(f"{context} has invalid schema ({'; '.join(parts)})")
    return value


def _expect_nonempty_name(value: Any, context: str) -> str:
    if not isinstance(value, str) or not _NAME_PATTERN.fullmatch(value):
        raise ModelValidationError(
            f"{context} must be a non-empty identifier ([A-Za-z_][A-Za-z0-9_]*)"
        )
    return value


def _expect_int(value: Any, context: str, *, minimum: int = 0) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value < minimum:
        qualifier = "positive" if minimum == 1 else f">= {minimum}"
        raise ModelValidationError(f"{context} must be an integer {qualifier}")
    return value


def _parse_model(model_path: Path) -> tuple[dict[str, Any], Any]:
    try:
        raw = json.loads(model_path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise ModelValidationError(f"model definition does not exist: {model_path}") from error
    except json.JSONDecodeError as error:
        raise ModelValidationError(f"model definition is not valid JSON: {error}") from error

    model = _expect_exact_keys(
        raw,
        {
            "schema_version",
            "model_id",
            "name",
            "description",
            "size_bytes",
            "bus_width",
            "software_interface",
            "registers",
        },
        "model",
    )
    if model["schema_version"] != _MODEL_SCHEMA_VERSION:
        raise ModelValidationError(
            f"model.schema_version must be {_MODEL_SCHEMA_VERSION}, got {model['schema_version']!r}"
        )
    _expect_nonempty_name(model["model_id"], "model.model_id")
    _expect_nonempty_name(model["name"], "model.name")
    if not isinstance(model["description"], str):
        raise ModelValidationError("model.description must be a string")
    size_bytes = _expect_int(model["size_bytes"], "model.size_bytes", minimum=1)
    bus_width = _expect_int(model["bus_width"], "model.bus_width", minimum=1)
    if bus_width != 32:
        raise ModelValidationError(
            f"model.bus_width must be exactly 32 for the canonical JSON schema, got {bus_width!r}"
        )
    if size_bytes % (bus_width // 8):
        raise ModelValidationError("model.size_bytes must be aligned to model.bus_width")
    software_interface = model["software_interface"]
    supported_interfaces = {"apb", "apb4", "vr"}
    if not isinstance(software_interface, str) or software_interface not in supported_interfaces:
        raise ModelValidationError(
            "model.software_interface must be exactly one of 'apb', 'apb4', or 'vr' "
            f"for the canonical JSON schema, got {software_interface!r}"
        )
    if not isinstance(model["registers"], list) or not model["registers"]:
        raise ModelValidationError("model.registers must be a non-empty array")

    # Imports happen only after roots and schema are validated, so malformed input cannot
    # start backend generation or publish a manifest.
    from . import Field, Register, RegSpace
    from .GlobalValues import get_field_access_by_value

    bank = RegSpace(
        model["name"],
        size_bytes,
        description=model["description"],
        software_interface=software_interface,
        bus_width=bus_width,
    )
    register_names: set[str] = set()
    for register_index, register_raw in enumerate(model["registers"]):
        context = f"model.registers[{register_index}]"
        register = _expect_exact_keys(
            register_raw, {"name", "offset_bytes", "width_bits", "fields"}, context
        )
        name = _expect_nonempty_name(register["name"], f"{context}.name")
        if name in register_names:
            raise ModelValidationError(f"{context}.name duplicates register {name!r}")
        register_names.add(name)
        offset = _expect_int(register["offset_bytes"], f"{context}.offset_bytes")
        width = _expect_int(register["width_bits"], f"{context}.width_bits", minimum=1)
        if width != bus_width:
            raise ModelValidationError(
                f"{context}.width_bits must equal model.bus_width for the existing RTL backend"
            )
        if not isinstance(register["fields"], list) or not register["fields"]:
            raise ModelValidationError(f"{context}.fields must be a non-empty array")
        dsl_register = Register(name, width, bus_width=bus_width)
        field_names: set[str] = set()
        for field_index, field_raw in enumerate(register["fields"]):
            field_context = f"{context}.fields[{field_index}]"
            field = _expect_exact_keys(
                field_raw,
                {"name", "lsb", "width_bits", "sw_access", "hw_access", "reset"},
                field_context,
            )
            field_name = _expect_nonempty_name(field["name"], f"{field_context}.name")
            if field_name in field_names:
                raise ModelValidationError(f"{field_context}.name duplicates field {field_name!r}")
            field_names.add(field_name)
            lsb = _expect_int(field["lsb"], f"{field_context}.lsb")
            field_width = _expect_int(field["width_bits"], f"{field_context}.width_bits", minimum=1)
            reset = _expect_int(field["reset"], f"{field_context}.reset")
            if not isinstance(field["sw_access"], str) or not isinstance(field["hw_access"], str):
                raise ModelValidationError(f"{field_context} access values must be strings")
            sw_access = get_field_access_by_value(field["sw_access"])
            hw_access = get_field_access_by_value(field["hw_access"])
            if sw_access is None or hw_access is None:
                raise ModelValidationError(
                    f"{field_context} access values must be supported FieldAccess values"
                )
            try:
                dsl_register.add(Field(field_name, field_width, sw_access, hw_access, reset), lsb)
            except (TypeError, ValueError, Exception) as error:
                raise ModelValidationError(f"{field_context} is invalid: {error}") from error
        try:
            bank.add(dsl_register, offset, name)
        except (TypeError, ValueError, Exception) as error:
            raise ModelValidationError(f"{context} is invalid: {error}") from error
    return model, bank


def _manifest_relative(path: Path, manifest_parent: Path) -> str:
    try:
        return path.resolve().relative_to(manifest_parent.resolve()).as_posix()
    except ValueError as error:
        raise ModelValidationError(
            f"artifact path escapes manifest directory: {path} is not below {manifest_parent}"
        ) from error


def _artifact_record(kind: str, path: Path, manifest_parent: Path) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeConfigurationError(f"required {kind} artifact is absent or empty: {path}")
    return {
        "class": kind,
        "status": "generated",
        "path": _manifest_relative(path, manifest_parent),
        "size_bytes": path.stat().st_size,
        "sha256": _sha256(path),
    }


def _write_json_atomically(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    encoded = json.dumps(payload, indent=2, sort_keys=True) + "\n"
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=path.parent, prefix=f".{path.name}.", delete=False
        ) as temporary:
            temporary_name = temporary.name
            temporary.write(encoded)
            temporary.flush()
        Path(temporary_name).replace(path)
    finally:
        if temporary_name is not None:
            Path(temporary_name).unlink(missing_ok=True)


def _reject_symlinked_target(path: Path, context: str) -> None:
    """Reject a target whose lexical path crosses an existing symlink."""

    lexical = path.expanduser()
    if not lexical.is_absolute():
        lexical = Path.cwd() / lexical
    current = Path(lexical.anchor)
    for part in lexical.parts[1:]:
        current /= part
        if current.is_symlink():
            raise RuntimeConfigurationError(f"{context} must not cross a symlink: {current}")


def _validate_publish_targets(output_dir: Path, manifest: Path) -> tuple[Path, Path, Path]:
    """Return safe resolved targets and the output path relative to the manifest parent."""

    _reject_symlinked_target(output_dir, "output_dir")
    _reject_symlinked_target(manifest, "manifest")
    output_root = output_dir.expanduser().resolve()
    manifest_path = manifest.expanduser().resolve()
    manifest_parent = manifest_path.parent
    if output_root == output_root.parent:
        raise RuntimeConfigurationError("output_dir must not be a filesystem root")
    try:
        manifest_parent.relative_to(output_root)
    except ValueError:
        pass
    else:
        raise RuntimeConfigurationError("manifest parent must not be inside output_dir")
    if not manifest_parent.exists():
        manifest_parent.mkdir(parents=True, exist_ok=True)
        _reject_symlinked_target(manifest_parent, "manifest parent")
    if not manifest_parent.is_dir():
        raise RuntimeConfigurationError(f"manifest parent must be an existing directory: {manifest_parent}")
    if output_root == manifest_parent:
        raise RuntimeConfigurationError("output_dir must be below, not equal to, the manifest parent")
    if output_root.exists() and not output_root.is_dir():
        raise RuntimeConfigurationError(f"output_dir must be a directory when it exists: {output_root}")
    if manifest_path.exists() and not manifest_path.is_file():
        raise RuntimeConfigurationError(f"manifest must be a regular file when it exists: {manifest_path}")
    if not output_root.parent.is_dir():
        raise RuntimeConfigurationError(
            f"output_dir parent must be an existing directory: {output_root.parent}"
        )
    try:
        output_relative = output_root.relative_to(manifest_parent)
    except ValueError as error:
        raise RuntimeConfigurationError(
            f"output_dir must be below manifest parent: {output_root} is outside {manifest_parent}"
        ) from error
    if output_relative == Path("."):
        raise RuntimeConfigurationError("output_dir must not equal the manifest parent")
    try:
        manifest_path.relative_to(output_root)
    except ValueError:
        pass
    else:
        raise RuntimeConfigurationError("manifest must not be inside output_dir")
    return output_root, manifest_path, output_relative


def _publish_replace(source: Path, target: Path) -> None:
    """One publish/rollback rename boundary, isolated for failure-injection tests."""

    os.replace(source, target)


def _normalize_staged_output_paths(stage_output_root: Path, final_output_root: Path) -> None:
    """Rebase backend-emitted absolute output paths before hashes are recorded.

    Some legacy aggregate headers and filelists embed the generation root.  Replacing the owned
    staging prefix with the final prefix makes staged output byte-identical to direct final-root
    generation while retaining the no-write-before-validation transaction boundary.
    """

    staged_prefix = str(stage_output_root).encode("utf-8")
    final_prefix = str(final_output_root).encode("utf-8")
    content_block = re.compile(
        r"^(?P<start>//\[UHDL\]Content Start \[md5:)[0-9a-f]{32}(?P<start_end>\])\n"
        r"(?P<body>.*)\n(?P<end>//\[UHDL\]Content End \[md5:)[0-9a-f]{32}(?P<end_end>\])\n*$",
        re.DOTALL,
    )

    for path in stage_output_root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        contents = path.read_bytes()
        if staged_prefix in contents:
            contents = contents.replace(staged_prefix, final_prefix)
        try:
            text = contents.decode("utf-8")
        except UnicodeDecodeError:
            path.write_bytes(contents)
            continue
        matched = content_block.fullmatch(text)
        if matched is not None:
            digest = hashlib.md5(matched.group("body").encode("utf-8")).hexdigest()
            text = (
                f"{matched.group('start')}{digest}{matched.group('start_end')}\n"
                f"{matched.group('body')}\n"
                f"{matched.group('end')}{digest}{matched.group('end_end')}\n\n"
            )
        path.write_text(text, encoding="utf-8")


def _rebase_artifact_paths(
    payload: dict[str, Any],
    *,
    stage_manifest_parent: Path,
    stage_output_root: Path,
    final_manifest_parent: Path,
    final_output_root: Path,
    final_generated_root: Path,
) -> dict[str, Any]:
    """Translate validated staged artifact paths into their final manifest-relative form."""

    rebased = json.loads(json.dumps(payload))
    for collection in ("artifacts", "auxiliary_artifacts"):
        for index, record in enumerate(rebased[collection]):
            staged_path = _manifest_relative_path(
                record["path"], stage_manifest_parent, f"{collection}[{index}]"
            )
            relative = staged_path.relative_to(stage_output_root)
            record["path"] = _manifest_relative(
                final_output_root / relative, final_manifest_parent
            )
    rebased["output_root"] = _manifest_relative(final_generated_root, final_manifest_parent)
    # Verification logs are not generated or validated in this transaction.  The sealed DAG
    # deliberately regenerates compile/behavior evidence after A03, so stale records must not
    # be carried forward merely because their old files still exist in a backup.
    rebased["verification_records"] = []
    return rebased


def _rollback_publish(
    *,
    stage_root: Path,
    output_root: Path,
    manifest_path: Path,
    stage_output_root: Path,
    stage_manifest_path: Path,
    candidate_manifest: Path | None,
    prior_output: Path | None,
    prior_manifest: Path | None,
    published_output: bool,
    published_manifest: bool,
) -> list[Exception]:
    """Restore prior finals without deleting either prior or newly generated evidence."""

    errors: list[Exception] = []
    failed_root = stage_root / ".failed_publish"
    try:
        failed_root.mkdir(parents=True, exist_ok=True)
    except OSError as error:
        return [error]

    if published_manifest and manifest_path.exists():
        try:
            _publish_replace(manifest_path, failed_root / manifest_path.name)
        except OSError as error:
            errors.append(error)
    if published_output and output_root.exists():
        try:
            failed_output = failed_root / "output"
            _publish_replace(output_root, failed_output)
        except OSError as error:
            errors.append(error)
    if prior_manifest is not None and prior_manifest.exists():
        try:
            _publish_replace(prior_manifest, manifest_path)
        except OSError as error:
            errors.append(error)
    if prior_output is not None and prior_output.exists():
        try:
            _publish_replace(prior_output, output_root)
        except OSError as error:
            errors.append(error)
    # A manifest candidate whose rename failed is owned temporary state; quarantine it so a
    # failed first publish never leaves a manifest-shaped file beside the final target.
    if candidate_manifest is not None and candidate_manifest.exists():
        try:
            _publish_replace(candidate_manifest, failed_root / candidate_manifest.name)
        except OSError as error:
            errors.append(error)
    if stage_manifest_path.exists():
        try:
            _publish_replace(stage_manifest_path, failed_root / stage_manifest_path.name)
        except OSError as error:
            errors.append(error)
    # Keep the original staged output, if it was never published, as owned quarantine evidence.
    if stage_output_root.exists() and not (stage_root / ".staged_output").exists():
        try:
            _publish_replace(stage_output_root, stage_root / ".staged_output")
        except OSError as error:
            errors.append(error)
    return errors


def _cleanup_successful_stage(stage_root: Path, manifest_parent: Path, output_name: str) -> None:
    """Remove only the exact owned stage after the final manifest has been validated."""

    try:
        relative = stage_root.relative_to(manifest_parent)
    except ValueError as error:
        raise RuntimeConfigurationError("owned generation stage escaped manifest parent") from error
    if (
        relative.parent != Path(".")
        or not stage_root.name.startswith(f".{output_name}.stage-")
        or stage_root.is_symlink()
        or not stage_root.is_dir()
    ):
        raise RuntimeConfigurationError(f"refusing to clean unsafe generation stage: {stage_root}")
    shutil.rmtree(stage_root)


def generate(model_definition: Path, output_dir: Path, manifest: Path) -> dict[str, Any]:
    """Generate, stage-validate, then transactionally publish a fixed-schema delivery bundle."""

    planner_root = resolve_address_planner_root()
    uhdl_root = resolve_uhdl_root()
    uhdl = load_canonical_uhdl()
    model_path = model_definition.resolve()
    output_root, manifest_path, output_relative = _validate_publish_targets(output_dir, manifest)
    model, bank = _parse_model(model_path)
    manifest_parent = manifest_path.parent
    stage_root = Path(
        tempfile.mkdtemp(prefix=f".{output_root.name}.stage-", dir=manifest_parent)
    )
    stage_output_root = stage_root / output_relative
    stage_manifest_path = stage_root / manifest_path.name
    prior_root = stage_root / ".prior"
    prior_output: Path | None = None
    prior_manifest: Path | None = None
    published_output = False
    published_manifest = False
    committed_and_validated = False
    candidate_manifest: Path | None = None
    try:
        stage_output_root.parent.mkdir(parents=True, exist_ok=True)
        # The existing backend owns the output shape. This wrapper adds no template or semantic
        # transformation; it only invokes it inside an owned same-filesystem stage.
        from . import GlobalValues

        prior_json_key = GlobalValues.key
        GlobalValues.key = 0
        try:
            bank.generate(str(stage_output_root))
        finally:
            GlobalValues.key = prior_json_key
        _normalize_staged_output_paths(stage_output_root, output_root)
        generated_root = stage_output_root / model["name"]
        rtl_candidates = sorted((generated_root / "rtl").rglob("*.v"))
        if not rtl_candidates:
            raise RuntimeConfigurationError(
                f"required register_rtl artifact is absent below {generated_root / 'rtl'}"
            )
        artifacts = [
            _artifact_record("register_rtl", rtl_candidates[0], stage_root),
            _artifact_record("c_header", generated_root / "chead" / f"addr_{model['name']}.h", stage_root),
            _artifact_record("verilog_header", generated_root / "vhead" / f"addr_{model['name']}.vh", stage_root),
            _artifact_record("ralf", generated_root / "ralf" / f"{model['name']}.ralf", stage_root),
            _artifact_record("json", generated_root / "html" / "data.json", stage_root),
        ]
        if tuple(artifact["class"] for artifact in artifacts) != _REQUIRED_CLASSES:
            raise RuntimeConfigurationError("required output-class inventory is incomplete")
        filelist = rtl_candidates[0].parent / "filelist.f"
        auxiliary = []
        if filelist.is_file() and filelist.stat().st_size:
            auxiliary.append(_artifact_record("filelist", filelist, stage_root))
        component_source = Path(inspect.getfile(Component)).resolve()
        staged_payload: dict[str, Any] = {
            "schema_version": 1,
            "model": {
                "id": model["model_id"],
                "path": str(model_path),
                "sha256": _sha256(model_path),
            },
            "runtime": {
                "address_planner": {
                    "root": str(planner_root),
                    "revision": _revision(planner_root),
                    "module": str(Path(sys.modules["address_planner"].__file__).resolve()),
                },
                "uhdl": {
                    "root": str(uhdl_root),
                    "revision": _revision(uhdl_root),
                    "module": str(Path(uhdl.__file__).resolve()),
                    "component": str(component_source),
                },
            },
            "output_root": _manifest_relative(generated_root, stage_root),
            "artifacts": artifacts,
            "auxiliary_artifacts": auxiliary,
            "verification_records": [],
        }
        _write_json_atomically(stage_manifest_path, staged_payload)
        inventory(stage_manifest_path)
        final_payload = _rebase_artifact_paths(
            staged_payload,
            stage_manifest_parent=stage_root,
            stage_output_root=stage_output_root,
            final_manifest_parent=manifest_parent,
            final_output_root=output_root,
            final_generated_root=output_root / model["name"],
        )

        if output_root.exists():
            prior_output = prior_root / "output"
            prior_output.parent.mkdir(parents=True, exist_ok=True)
            _publish_replace(output_root, prior_output)
        if manifest_path.exists():
            prior_manifest = prior_root / manifest_path.name
            prior_manifest.parent.mkdir(parents=True, exist_ok=True)
            _publish_replace(manifest_path, prior_manifest)
        _publish_replace(stage_output_root, output_root)
        published_output = True
        candidate_manifest = manifest_parent / f".{manifest_path.name}.pending-{stage_root.name}"
        _write_json_atomically(candidate_manifest, final_payload)
        inventory(candidate_manifest)
        _publish_replace(candidate_manifest, manifest_path)
        published_manifest = True
        inventory(manifest_path)
        committed_and_validated = True
        _cleanup_successful_stage(stage_root, manifest_parent, output_root.name)
        final_payload["manifest_sha256"] = _sha256(manifest_path)
        return final_payload
    except Exception as error:
        if committed_and_validated:
            raise
        rollback_errors = _rollback_publish(
            stage_root=stage_root,
            output_root=output_root,
            manifest_path=manifest_path,
            stage_output_root=stage_output_root,
            stage_manifest_path=stage_manifest_path,
            candidate_manifest=candidate_manifest,
            prior_output=prior_output,
            prior_manifest=prior_manifest,
            published_output=published_output,
            published_manifest=published_manifest,
        )
        if rollback_errors:
            raise RuntimeConfigurationError(
                "generation publish failed and rollback did not complete: "
                + "; ".join(str(rollback_error) for rollback_error in rollback_errors)
            ) from error
        raise


def _manifest_error(message: str) -> ManifestValidationError:
    return ManifestValidationError(f"delivery manifest validation failed: {message}")


def _manifest_relative_path(value: Any, manifest_parent: Path, context: str) -> Path:
    """Resolve one manifest path without allowing traversal or an escaped symlink."""

    if not isinstance(value, str) or not value or value == ".":
        raise _manifest_error(f"{context}.path must be a non-empty relative string")
    declared = Path(value)
    path_parts = value.replace("\\", "/").split("/")
    if declared.is_absolute() or PureWindowsPath(value).is_absolute() or ".." in path_parts:
        raise _manifest_error(f"{context}.path must be relative and must not contain '..'")
    candidate = manifest_parent / declared
    try:
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(manifest_parent.resolve())
    except (OSError, RuntimeError, ValueError) as error:
        raise _manifest_error(
            f"{context}.path escapes the manifest directory or cannot be resolved: {value}"
        ) from error
    return resolved


def _validate_manifest_file(path: Path, context: str) -> tuple[int, str]:
    try:
        file_stat = path.stat()
    except OSError as error:
        raise _manifest_error(f"{context}.path cannot be stat'ed: {path}") from error
    if not stat.S_ISREG(file_stat.st_mode) or file_stat.st_size <= 0:
        raise _manifest_error(f"{context}.path must resolve to a non-empty regular file")
    return file_stat.st_size, _sha256(path)


def _validate_artifact_record(
    raw: Any,
    *,
    context: str,
    manifest_parent: Path,
    output_root: Path,
    required: bool,
) -> tuple[str, Path]:
    if not isinstance(raw, dict):
        raise _manifest_error(f"{context} must be an object")
    actual = set(raw)
    if actual != _ARTIFACT_KEYS:
        missing = sorted(_ARTIFACT_KEYS - actual)
        unknown = sorted(actual - _ARTIFACT_KEYS)
        detail = []
        if missing:
            detail.append(f"missing keys: {', '.join(missing)}")
        if unknown:
            detail.append(f"unknown keys: {', '.join(unknown)}")
        raise _manifest_error(f"{context} has invalid schema ({'; '.join(detail)})")
    kind = raw["class"]
    if not isinstance(kind, str) or not _NAME_PATTERN.fullmatch(kind):
        raise _manifest_error(f"{context}.class must be a non-empty identifier")
    if raw["status"] != "generated":
        raise _manifest_error(f"{context}.status must be 'generated'")
    resolved = _manifest_relative_path(raw["path"], manifest_parent, context)
    try:
        resolved.relative_to(output_root)
    except ValueError as error:
        raise _manifest_error(f"{context}.path must be below output_root") from error
    size, digest = _validate_manifest_file(resolved, context)
    recorded_size = raw["size_bytes"]
    if not isinstance(recorded_size, int) or isinstance(recorded_size, bool) or recorded_size <= 0:
        raise _manifest_error(f"{context}.size_bytes must be a positive integer")
    if recorded_size != size:
        raise _manifest_error(
            f"{context}.size_bytes mismatch: manifest={recorded_size}, actual={size}"
        )
    recorded_digest = raw["sha256"]
    if not isinstance(recorded_digest, str) or not _SHA256_PATTERN.fullmatch(recorded_digest):
        raise _manifest_error(f"{context}.sha256 must be a lowercase 64-hex digest")
    if recorded_digest != digest:
        raise _manifest_error(f"{context}.sha256 mismatch")
    if required and kind not in _REQUIRED_CLASSES:
        raise _manifest_error(f"{context}.class is not a required output class: {kind}")
    return kind, resolved


def _required_artifact_hashes(artifacts: list[dict[str, Any]]) -> dict[str, str]:
    """Return the stable required-artifact fingerprint used by verification records."""

    return {record["class"]: record["sha256"] for record in artifacts}


def _validate_verification_record(
    raw: Any,
    *,
    context: str,
    manifest_parent: Path,
    output_root: Path,
    model_sha256: str | None = None,
    required_artifact_sha256: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Validate one replay-stable verification record without mutating its manifest."""

    if not isinstance(raw, dict) or "kind" not in raw:
        raise _manifest_error(f"{context} has invalid schema")
    if not isinstance(raw["kind"], str) or not _NAME_PATTERN.fullmatch(raw["kind"]):
        raise _manifest_error(f"{context}.kind must be an identifier")
    expected_keys = (
        _BEHAVIOR_VERIFICATION_RECORD_KEYS
        if raw["kind"] == "register_behavior"
        else _VERIFICATION_RECORD_KEYS
    )
    if set(raw) != expected_keys:
        raise _manifest_error(f"{context} has invalid schema")
    tool = raw["tool"]
    if not isinstance(tool, dict) or set(tool) != _VERIFICATION_TOOL_KEYS:
        raise _manifest_error(f"{context}.tool has invalid schema")
    if not all(isinstance(tool[key], str) and tool[key] for key in _VERIFICATION_TOOL_KEYS):
        raise _manifest_error(f"{context}.tool values must be non-empty strings")
    executable = Path(tool["path"])
    if not executable.is_absolute() or not executable.is_file():
        raise _manifest_error(f"{context}.tool.path must name an existing absolute executable")
    argv = raw["argv"]
    if not isinstance(argv, list) or not argv or any(not isinstance(arg, str) or not arg for arg in argv):
        raise _manifest_error(f"{context}.argv must be a non-empty string array")
    if Path(argv[0]).resolve() != executable.resolve():
        raise _manifest_error(f"{context}.argv[0] must match tool.path")
    if not isinstance(raw["exit_code"], int) or isinstance(raw["exit_code"], bool) or raw["exit_code"] < 0:
        raise _manifest_error(f"{context}.exit_code must be a non-negative integer")
    inputs = raw["inputs"]
    if not isinstance(inputs, dict) or set(inputs) != _VERIFICATION_INPUT_KEYS:
        raise _manifest_error(f"{context}.inputs has invalid schema")
    input_model_hash = inputs["model_sha256"]
    if not isinstance(input_model_hash, str) or not _SHA256_PATTERN.fullmatch(input_model_hash):
        raise _manifest_error(f"{context}.inputs.model_sha256 must be a lowercase SHA-256")
    input_artifact_hashes = inputs["required_artifact_sha256"]
    if (
        not isinstance(input_artifact_hashes, dict)
        or set(input_artifact_hashes) != set(_REQUIRED_CLASSES)
        or any(
            not isinstance(digest, str) or not _SHA256_PATTERN.fullmatch(digest)
            for digest in input_artifact_hashes.values()
        )
    ):
        raise _manifest_error(f"{context}.inputs.required_artifact_sha256 is invalid")
    if model_sha256 is not None and input_model_hash != model_sha256:
        raise _manifest_error(f"{context}.inputs.model_sha256 does not match the manifest model")
    if required_artifact_sha256 is not None and input_artifact_hashes != required_artifact_sha256:
        raise _manifest_error(f"{context}.inputs.required_artifact_sha256 does not match manifest artifacts")
    log = raw["log"]
    if not isinstance(log, dict) or set(log) != _VERIFICATION_LOG_KEYS:
        raise _manifest_error(f"{context}.log has invalid schema")
    resolved_log = _manifest_relative_path(log["path"], manifest_parent, f"{context}.log")
    try:
        resolved_log.relative_to(output_root)
    except ValueError as error:
        raise _manifest_error(f"{context}.log.path must be below output_root") from error
    log_size, log_digest = _validate_manifest_file(resolved_log, f"{context}.log")
    if log["size_bytes"] != log_size or log["sha256"] != log_digest:
        raise _manifest_error(f"{context}.log size or SHA-256 mismatch")
    if raw["kind"] == "register_behavior":
        run = raw["run"]
        if not isinstance(run, dict) or set(run) != _VERIFICATION_RUN_KEYS:
            raise _manifest_error(f"{context}.run has invalid schema")
        run_argv = run["argv"]
        if (
            not isinstance(run_argv, list)
            or not run_argv
            or any(not isinstance(arg, str) or not arg for arg in run_argv)
        ):
            raise _manifest_error(f"{context}.run.argv must be a non-empty string array")
        run_executable = Path(run_argv[0])
        if not run_executable.is_absolute() or not run_executable.is_file() or not os.access(run_executable, os.X_OK):
            raise _manifest_error(f"{context}.run.argv[0] must name an existing absolute executable")
        if not isinstance(run["exit_code"], int) or isinstance(run["exit_code"], bool) or run["exit_code"] < 0:
            raise _manifest_error(f"{context}.run.exit_code must be a non-negative integer")
        supporting = raw["supporting_artifacts"]
        if not isinstance(supporting, list) or len(supporting) != 2:
            raise _manifest_error(f"{context}.supporting_artifacts must contain testbench and filelist")
        supporting_classes: set[str] = set()
        for index, record in enumerate(supporting):
            kind, _resolved = _validate_artifact_record(
                record,
                context=f"{context}.supporting_artifacts[{index}]",
                manifest_parent=manifest_parent,
                output_root=output_root,
                required=False,
            )
            supporting_classes.add(kind)
        if supporting_classes != {"testbench", "filelist"}:
            raise _manifest_error(f"{context}.supporting_artifacts must contain unique testbench and filelist records")
    return raw


def _preserved_verification_records(
    manifest_path: Path,
    *,
    output_root: Path,
    model_sha256: str,
    artifacts: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Keep only prior records whose inputs and evidence still validate after generation."""

    if not manifest_path.is_file():
        return []
    try:
        old_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        records = old_manifest.get("verification_records", [])
        if not isinstance(records, list):
            return []
        expected_hashes = _required_artifact_hashes(artifacts)
        valid: list[dict[str, Any]] = []
        seen_kinds: set[str] = set()
        for index, record in enumerate(records):
            checked = _validate_verification_record(
                record,
                context=f"verification_records[{index}]",
                manifest_parent=manifest_path.parent,
                output_root=output_root,
                model_sha256=model_sha256,
                required_artifact_sha256=expected_hashes,
            )
            if checked["kind"] in seen_kinds:
                return []
            seen_kinds.add(checked["kind"])
            valid.append(checked)
        return valid
    except (OSError, ValueError, ManifestValidationError):
        return []


def inventory(manifest: Path) -> dict[str, Any]:
    """Read and strictly validate a generated delivery manifest without modifying it."""

    manifest_path = manifest.resolve()
    manifest_parent = manifest_path.parent
    try:
        raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise _manifest_error(f"does not exist: {manifest_path}") from error
    except UnicodeDecodeError as error:
        raise _manifest_error(f"is not UTF-8 JSON: {manifest_path}") from error
    except json.JSONDecodeError as error:
        raise _manifest_error(f"is not valid JSON: {error}") from error
    if not isinstance(raw, dict):
        raise _manifest_error("top level must be an object")
    actual = set(raw)
    if actual != _MANIFEST_KEYS:
        missing = sorted(_MANIFEST_KEYS - actual)
        unknown = sorted(actual - _MANIFEST_KEYS)
        detail = []
        if missing:
            detail.append(f"missing keys: {', '.join(missing)}")
        if unknown:
            detail.append(f"unknown keys: {', '.join(unknown)}")
        raise _manifest_error(f"top-level schema is invalid ({'; '.join(detail)})")
    if (
        not isinstance(raw["schema_version"], int)
        or isinstance(raw["schema_version"], bool)
        or raw["schema_version"] != 1
    ):
        raise _manifest_error(f"schema_version must be 1, got {raw['schema_version']!r}")
    if not isinstance(raw["model"], dict) or not isinstance(raw["runtime"], dict):
        raise _manifest_error("model and runtime must be objects")
    output_root = _manifest_relative_path(raw["output_root"], manifest_parent, "output_root")
    if not output_root.is_dir():
        raise _manifest_error("output_root must resolve to a directory")
    artifacts = raw["artifacts"]
    if not isinstance(artifacts, list):
        raise _manifest_error("artifacts must be an array")
    required_classes: list[str] = []
    seen_paths: set[Path] = set()
    for index, record in enumerate(artifacts):
        kind, resolved = _validate_artifact_record(
            record,
            context=f"artifacts[{index}]",
            manifest_parent=manifest_parent,
            output_root=output_root,
            required=True,
        )
        if resolved in seen_paths:
            raise _manifest_error(f"artifacts[{index}].path duplicates another artifact path")
        seen_paths.add(resolved)
        required_classes.append(kind)
    if set(required_classes) != set(_REQUIRED_CLASSES) or len(required_classes) != len(_REQUIRED_CLASSES):
        raise _manifest_error(
            "artifacts must contain each required class exactly once: "
            + ", ".join(_REQUIRED_CLASSES)
        )
    auxiliary = raw["auxiliary_artifacts"]
    if not isinstance(auxiliary, list):
        raise _manifest_error("auxiliary_artifacts must be an array")
    seen_auxiliary_classes: set[str] = set()
    for index, record in enumerate(auxiliary):
        kind, resolved = _validate_artifact_record(
            record,
            context=f"auxiliary_artifacts[{index}]",
            manifest_parent=manifest_parent,
            output_root=output_root,
            required=False,
        )
        if kind in _REQUIRED_CLASSES:
            raise _manifest_error(f"auxiliary_artifacts[{index}].class duplicates a required class")
        if kind in seen_auxiliary_classes:
            raise _manifest_error(f"auxiliary_artifacts[{index}].class is duplicated")
        if resolved in seen_paths:
            raise _manifest_error(f"auxiliary_artifacts[{index}].path duplicates another artifact path")
        seen_auxiliary_classes.add(kind)
        seen_paths.add(resolved)
    model_sha256 = raw["model"].get("sha256")
    if not isinstance(model_sha256, str) or not _SHA256_PATTERN.fullmatch(model_sha256):
        raise _manifest_error("model.sha256 must be a lowercase SHA-256")
    verification_records = raw["verification_records"]
    if not isinstance(verification_records, list):
        raise _manifest_error("verification_records must be an array")
    required_artifact_sha256 = _required_artifact_hashes(artifacts)
    seen_verification_kinds: set[str] = set()
    for index, record in enumerate(verification_records):
        checked = _validate_verification_record(
            record,
            context=f"verification_records[{index}]",
            manifest_parent=manifest_parent,
            output_root=output_root,
            model_sha256=model_sha256,
            required_artifact_sha256=required_artifact_sha256,
        )
        if checked["kind"] in seen_verification_kinds:
            raise _manifest_error(f"verification_records[{index}].kind is duplicated")
        seen_verification_kinds.add(checked["kind"])
    return {
        "manifest": str(manifest_path),
        "manifest_sha256": _sha256(manifest_path),
        "output_root": str(output_root),
        "required_classes": list(_REQUIRED_CLASSES),
        "artifact_count": len(artifacts),
        "auxiliary_artifact_count": len(auxiliary),
        "verification_record_count": len(verification_records),
    }


def _consistency_error(message: str) -> RuntimeConfigurationError:
    return RuntimeConfigurationError(f"cross-output consistency failed: {message}")


def _consistency_model(raw: dict[str, Any]) -> list[dict[str, Any]]:
    """Read the immutable model named by a validated manifest, without generation."""

    model_record = raw["model"]
    model_path = Path(model_record.get("path", ""))
    if not model_path.is_file() or _sha256(model_path) != model_record.get("sha256"):
        raise _consistency_error("manifest model path is absent or its SHA-256 does not match")
    try:
        model = json.loads(model_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise _consistency_error(f"cannot read manifest model: {error}") from error
    registers = model.get("registers") if isinstance(model, dict) else None
    if not isinstance(registers, list) or not registers:
        raise _consistency_error("manifest model has no register array")
    return registers


def _header_macros(path: Path) -> dict[str, int]:
    macros: dict[str, int] = {}
    pattern = re.compile(
        r"^[ \t]*(?:#|`)define[ \t]+([A-Z][A-Z0-9_]*)[ \t]+([^ \t\r\n/]+)",
        re.MULTILINE,
    )
    for name, value in pattern.findall(path.read_text(encoding="utf-8")):
        literal = re.sub(r"^\d+'h", "0x", value.lower()).replace("'h", "0x")
        try:
            macros[name] = int(literal, 0)
        except ValueError as error:
            raise _consistency_error(f"{path.name} macro {name} has non-integer value {value!r}") from error
    return macros


def _expect_header_fields(
    macros: dict[str, int], registers: list[dict[str, Any]], representation: str
) -> list[str]:
    def value_for(name: str) -> int | None:
        if name in macros:
            return macros[name]
        matches = [value for macro, value in macros.items() if macro.endswith(f"_{name}")]
        return matches[0] if len(matches) == 1 else None

    errors: list[str] = []
    for register in registers:
        reg_name = register["name"].upper()
        if value_for(f"{reg_name}_OFFSET") != register["offset_bytes"]:
            errors.append(f"{register['name']} address")
        for field in register["fields"]:
            prefix = f"{reg_name}_{field['name'].upper()}"
            for suffix, expected in (
                ("OFFSET", field["lsb"]),
                ("WIDTH", field["width_bits"]),
                ("RST_VAL", field["reset"]),
            ):
                if value_for(f"{prefix}_{suffix}") != expected:
                    errors.append(f"{register['name']}.{field['name']} {suffix.lower()}")
    if errors:
        raise _consistency_error(f"{representation}: " + ", ".join(errors))
    return []


def _expect_c_padding(path: Path, registers: list[dict[str, Any]]) -> None:
    text = path.read_text(encoding="utf-8")
    for register in registers:
        name = register["name"].upper()
        qualified = rf"(?:[A-Z][A-Z0-9_]*_)?{re.escape(name)}"
        match = re.search(
            rf"Definition of reg\s+{qualified}.*?typedef union\s*\{{\s*struct\s*\{{(?P<body>.*?)\}}\s*bits;\s*uint(?:32|64)_t\s+val;\s*\}}\s*{qualified}\s*;",
            text,
            re.DOTALL,
        )
        if match is None:
            raise _consistency_error(f"c_header: missing union for {register['name']}")
        actual = [(entry[0], int(entry[1])) for entry in re.findall(r"(?:u?int\d+_t)\s+(\w+)\s*:\s*(\d+)", match.group("body"))]
        expected: list[tuple[str, int]] = []
        cursor = 0
        for field in sorted(register["fields"], key=lambda item: item["lsb"]):
            if field["lsb"] > cursor:
                expected.append((f"reserved_{cursor}", field["lsb"] - cursor))
            expected.append((field["name"], field["width_bits"]))
            cursor = field["lsb"] + field["width_bits"]
        if cursor < register["width_bits"]:
            expected.append((f"reserved_{cursor}", register["width_bits"] - cursor))
        if actual != expected:
            raise _consistency_error(
                f"c_header: {register['name']} bitfield layout {actual!r} does not include explicit model gaps {expected!r}"
            )


def _expect_vhead_layout(path: Path, registers: list[dict[str, Any]]) -> None:
    text = path.read_text(encoding="utf-8")
    for register in registers:
        name = register["name"].upper()
        qualified = rf"(?:[A-Z][A-Z0-9_]*_)?{re.escape(name)}"
        match = re.search(
            rf"Definition of reg\s+{qualified}.*?typedef union packed\s*\{{\s*struct packed\s*\{{(?P<body>.*?)\}}\s*bits;\s*logic\s*\[[^\]]+\]\s+val;\s*\}}\s*{qualified}\s*;",
            text,
            re.DOTALL,
        )
        if match is None:
            raise _consistency_error(f"verilog_header: missing packed union for {register['name']}")
        actual = re.findall(r"logic\s*\[[^\]]+\]\s+(\w+)\s*;", match.group("body"))
        expected: list[tuple[int, str]] = []
        cursor = 0
        for field in sorted(register["fields"], key=lambda item: item["lsb"]):
            if field["lsb"] > cursor:
                expected.append((cursor, f"reserved_{cursor}"))
            expected.append((field["lsb"], field["name"]))
            cursor = field["lsb"] + field["width_bits"]
        if cursor < register["width_bits"]:
            expected.append((cursor, f"reserved_{cursor}"))
        expected_names = [entry[1] for entry in reversed(expected)]
        if actual != expected_names:
            raise _consistency_error(
                f"verilog_header: {register['name']} packed members {actual!r} are not MSB-first {expected_names!r}"
            )


def _expect_json(path: Path, registers: list[dict[str, Any]]) -> None:
    try:
        roots = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise _consistency_error(f"json artifact is invalid: {error}") from error
    if not isinstance(roots, list):
        raise _consistency_error("json artifact root must be an array")
    nodes: dict[str, dict[str, Any]] = {}
    stack = list(roots)
    while stack:
        node = stack.pop()
        if isinstance(node, dict):
            if node.get("type") == "reg" and isinstance(node.get("name"), str):
                nodes[node["name"]] = node
            children = node.get("children", [])
            if isinstance(children, list):
                stack.extend(children)
    access_values = {member.name: member.value for member in __import__("address_planner.GlobalValues", fromlist=["FieldAccess"]).FieldAccess}
    for register in registers:
        node = nodes.get(register["name"])
        if node is None or int(str(node.get("start_addr")), 0) != register["offset_bytes"]:
            raise _consistency_error(f"json: register {register['name']} name/address mismatch")
        actual_fields = {field.get("name"): field for field in node.get("fields", []) if isinstance(field, dict)}
        for field in register["fields"]:
            actual = actual_fields.get(field["name"])
            if actual is None:
                raise _consistency_error(f"json: field {register['name']}.{field['name']} missing")
            position = re.fullmatch(r"\[(\d+):(\d+)\]", str(actual.get("Position")))
            if position is None or int(position.group(2)) != field["lsb"] or int(position.group(1)) - int(position.group(2)) + 1 != field["width_bits"]:
                raise _consistency_error(f"json: field {register['name']}.{field['name']} position/width mismatch")
            if actual.get("Software Access") not in access_values or access_values[actual["Software Access"]] != field["sw_access"]:
                raise _consistency_error(f"json: field {register['name']}.{field['name']} SW access mismatch")
            if actual.get("Hardware Access") not in access_values or access_values[actual["Hardware Access"]] != field["hw_access"]:
                raise _consistency_error(f"json: field {register['name']}.{field['name']} HW access mismatch")
            reset_value = actual.get("Default Value", actual.get("defaut_value"))
            try:
                parsed_reset = int(str(reset_value), 0)
            except (TypeError, ValueError):
                parsed_reset = reset_value
            if parsed_reset != field["reset"]:
                raise _consistency_error(f"json: field {register['name']}.{field['name']} reset mismatch")


def _expect_ralf(path: Path, registers: list[dict[str, Any]]) -> None:
    text = path.read_text(encoding="utf-8")
    sections = re.split(r"(?=^\s*register\s+)", text, flags=re.MULTILINE)
    parsed: dict[str, tuple[int, dict[str, tuple[int, int, str, int]]]] = {}
    field_pattern = re.compile(r"field\s+(\w+)(?:\s+\([^)]*\))?\s+@(\d+)\s*\{\s*bits\s+(\d+);\s*access\s+(\w+);\s*reset\s+(\d+);", re.DOTALL)
    for section in sections:
        register = re.match(r"\s*register\s+(\w+)\s+@([^\s]+)\s*\{", section)
        if register is None:
            continue
        parsed[register.group(1)] = (
            int(re.sub(r"^\d+'h", "0x", register.group(2).lower()).replace("'h", "0x"), 0),
            {name: (int(lsb), int(width), access.upper(), int(reset)) for name, lsb, width, access, reset in field_pattern.findall(section)},
        )
    for register in registers:
        actual = parsed.get(register["name"])
        if actual is None or actual[0] != register["offset_bytes"]:
            raise _consistency_error(f"ralf: register {register['name']} name/address mismatch")
        for field in register["fields"]:
            if actual[1].get(field["name"]) != (field["lsb"], field["width_bits"], field["sw_access"], field["reset"]):
                raise _consistency_error(f"ralf: field {register['name']}.{field['name']} mismatch")


def _rtl_literal(value: str) -> int:
    literal = value.strip().lower()
    return int(re.sub(r"^\d+'([bhd])", lambda item: {"b": "0b", "h": "0x", "d": ""}[item.group(1)], literal), 0)


def _expect_rtl(path: Path, registers: list[dict[str, Any]]) -> None:
    """Check stable generated RTL patterns, including executable access semantics."""

    text = path.read_text(encoding="utf-8")
    for register in registers:
        reg = register["name"]
        address_pattern = rf"rreq_addr\s*==\s*32'h{register['offset_bytes']:x}"
        if not re.search(address_pattern, text):
            raise _consistency_error(f"register_rtl: {reg} read address decode mismatch")
        rdat = re.search(rf"assign\s+{re.escape(reg)}_rdat\s*=\s*\{{(?P<body>[^;]+)\}}\s*;", text)
        if rdat is None:
            raise _consistency_error(f"register_rtl: {reg} read-data packing missing")
        declarations = {
            name: int(msb) + 1
            for msb, name in re.findall(r"(?:reg|wire)\s*\[(\d+):0\]\s+(\w+)\s*;", text)
        }
        lsb_by_symbol: dict[str, int] = {}
        cursor = 0
        for token in reversed([part.strip() for part in rdat.group("body").split(",")]):
            zero = re.fullmatch(r"(\d+)'b0", token)
            if zero is not None:
                cursor += int(zero.group(1))
            elif token in declarations:
                lsb_by_symbol[token] = cursor
                cursor += declarations[token]
            else:
                raise _consistency_error(f"register_rtl: {reg} has unparseable packed token {token!r}")
        if cursor != register["width_bits"]:
            raise _consistency_error(f"register_rtl: {reg} read-data width mismatch")
        for field in register["fields"]:
            symbol = f"{reg}_{field['name']}"
            if declarations.get(symbol) != field["width_bits"] or lsb_by_symbol.get(symbol) != field["lsb"]:
                raise _consistency_error(f"register_rtl: {reg}.{field['name']} slice/width mismatch")
            reset = re.search(rf"if\s*\(~rst_n\)\s+{re.escape(symbol)}\s*<=\s*([^;]+);", text)
            if reset is None or _rtl_literal(reset.group(1)) != field["reset"]:
                raise _consistency_error(f"register_rtl: {reg}.{field['name']} reset mismatch")
            sw_enable = f"{symbol}_sw_wren"
            if field["sw_access"] == "RO":
                if sw_enable in text:
                    raise _consistency_error(f"register_rtl: {reg}.{field['name']} accepts software writes despite RO")
            elif field["sw_access"] == "RW":
                if not re.search(rf"if\s*\({re.escape(sw_enable)}\)\s+{re.escape(symbol)}\s*<=\s*{re.escape(symbol)}_field_wdat;", text):
                    raise _consistency_error(f"register_rtl: {reg}.{field['name']} RW write path mismatch")
            elif field["sw_access"] == "W1C":
                if not re.search(rf"if\s*\({re.escape(sw_enable)}\)\s+{re.escape(symbol)}\s*<=\s*\(\(~{re.escape(symbol)}_field_wdat\)\s*&\s*{re.escape(symbol)}\);", text):
                    raise _consistency_error(f"register_rtl: {reg}.{field['name']} W1C write path mismatch")
            else:
                raise _consistency_error(f"register_rtl: unsupported structural access check {field['sw_access']}")
            hw_enable = f"{symbol}_wena"
            if field["hw_access"] == "RW":
                if not re.search(rf"if\s*\({re.escape(hw_enable)}\)\s+{re.escape(symbol)}\s*<=\s*{re.escape(symbol)}_wdat;", text):
                    raise _consistency_error(f"register_rtl: {reg}.{field['name']} HW RW path mismatch")
            elif field["hw_access"] == "RO":
                if hw_enable in text:
                    raise _consistency_error(f"register_rtl: {reg}.{field['name']} accepts hardware writes despite RO")
            else:
                raise _consistency_error(f"register_rtl: unsupported structural HW access check {field['hw_access']}")


def consistency(manifest: Path) -> dict[str, Any]:
    """Cross-check generated, manifest-recorded artifacts without regeneration or manifest writes."""

    inventory(manifest)
    manifest_path = manifest.resolve()
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    output_root = _manifest_relative_path(raw["output_root"], manifest_path.parent, "output_root")
    artifact_paths = {
        record["class"]: _manifest_relative_path(record["path"], manifest_path.parent, record["class"])
        for record in raw["artifacts"]
    }
    registers = _consistency_model(raw)
    _expect_rtl(artifact_paths["register_rtl"], registers)
    _expect_json(artifact_paths["json"], registers)
    _expect_header_fields(_header_macros(artifact_paths["c_header"]), registers, "c_header")
    _expect_c_padding(artifact_paths["c_header"], registers)
    _expect_header_fields(_header_macros(artifact_paths["verilog_header"]), registers, "verilog_header")
    _expect_vhead_layout(artifact_paths["verilog_header"], registers)
    _expect_ralf(artifact_paths["ralf"], registers)
    report = {
        "schema_version": 1,
        "manifest": {"path": str(manifest_path), "sha256": _sha256(manifest_path)},
        "model": {"path": raw["model"]["path"], "sha256": raw["model"]["sha256"]},
        "representations": [
            {"class": "json", "represented": ["register_name", "register_address", "field_name", "field_lsb", "field_width", "sw_access", "hw_access", "reset"], "not_represented": []},
            {"class": "c_header", "represented": ["register_name", "register_address", "field_name", "field_lsb", "field_width", "reset"], "not_represented": ["sw_access", "hw_access"]},
            {"class": "verilog_header", "represented": ["register_name", "register_address", "field_name", "field_lsb", "field_width", "reset"], "not_represented": ["sw_access", "hw_access"]},
            {"class": "ralf", "represented": ["register_name", "register_address", "field_name", "field_lsb", "field_width", "sw_access", "reset"], "not_represented": ["hw_access"]},
            {"class": "register_rtl", "represented": ["register_name", "register_address", "field_name", "field_lsb", "field_width", "reset"], "inferred": ["sw_access", "hw_access"], "not_represented": [], "reason": "Addresses, slices, and resets are parsed from stable generated RTL patterns; access is verified from its executable write paths."},
        ],
        "register_count": len(registers),
        "result": "pass",
    }
    report_path = output_root / "verification" / "consistency_report.json"
    _write_json_atomically(report_path, report)
    return {"report": str(report_path), "sha256": _sha256(report_path), "result": "pass"}


def compile_rtl(manifest: Path, tool: str) -> dict[str, Any]:
    """Run strict lint over the complete generated RTL filelist and record the replay evidence."""

    inventory(manifest)
    manifest_path = manifest.resolve()
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    output_root = _manifest_relative_path(raw["output_root"], manifest_path.parent, "output_root")
    filelists = [record for record in raw["auxiliary_artifacts"] if record["class"] == "filelist"]
    if len(filelists) != 1:
        raise RuntimeConfigurationError("manifest must contain exactly one complete RTL filelist")
    filelist = _manifest_relative_path(filelists[0]["path"], manifest_path.parent, "filelist")
    executable = shutil.which(tool)
    if executable is None:
        raise RuntimeConfigurationError(f"requested compile tool is not available on PATH: {tool}")
    tool_path = Path(executable).resolve()
    try:
        version = subprocess.check_output(
            [str(tool_path), "--version"], text=True, stderr=subprocess.STDOUT, timeout=10
        ).splitlines()[0]
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired, IndexError) as error:
        raise RuntimeConfigurationError(f"cannot determine {tool_path} version: {error}") from error
    argv = [str(tool_path), "--lint-only", "-Wall", "-f", str(filelist)]
    log_path = output_root / "verification" / f"strict_compile_{tool_path.name}.log"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_name: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=log_path.parent, prefix=f".{log_path.name}.", delete=False
        ) as handle:
            temporary_name = handle.name
            handle.write(json.dumps({"argv": argv, "tool_version": version}, sort_keys=True) + "\n")
            handle.flush()
            completed = subprocess.run(argv, stdout=handle, stderr=subprocess.STDOUT, text=True, check=False)
        Path(temporary_name).replace(log_path)
        temporary_name = None
    finally:
        if temporary_name is not None:
            Path(temporary_name).unlink(missing_ok=True)
    if not log_path.is_file() or log_path.stat().st_size <= 0:
        raise RuntimeConfigurationError(f"compile log was not created: {log_path}")
    record = {
        "kind": "strict_compile",
        "tool": {"requested": tool, "path": str(tool_path), "version": version},
        "argv": argv,
        "exit_code": completed.returncode,
        "inputs": {
            "model_sha256": raw["model"]["sha256"],
            "required_artifact_sha256": _required_artifact_hashes(raw["artifacts"]),
        },
        "log": {
            "path": _manifest_relative(log_path, manifest_path.parent),
            "size_bytes": log_path.stat().st_size,
            "sha256": _sha256(log_path),
        },
    }
    raw["verification_records"] = [
        prior for prior in raw["verification_records"] if prior["kind"] != record["kind"]
    ] + [record]
    _write_json_atomically(manifest_path, raw)
    return {
        "manifest": str(manifest_path),
        "manifest_sha256": _sha256(manifest_path),
        "tool": str(tool_path),
        "version": version,
        "argv": argv,
        "exit_code": completed.returncode,
        "log": str(log_path),
        "log_sha256": record["log"]["sha256"],
    }


def _representative_behavior_spec(model_path: Path) -> None:
    """Reject a model other than the sealed APB behavior fixture.

    The generated testbench intentionally exercises the fixed representative model rather
    than claiming a generic bus-functional testbench for every possible DSL construct.
    """

    try:
        model = json.loads(model_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeConfigurationError(f"cannot read behavior model {model_path}: {error}") from error
    registers = {entry.get("name"): entry for entry in model.get("registers", [])}
    expected = {
        "control": (0, {"enable": ("RW", "RO", 1), "mode": ("RW", "RO", 2)}),
        "status": (4, {"ready": ("RO", "RW", 0)}),
        "events": (8, {"pending": ("W1C", "RW", 10)}),
    }
    if set(registers) != set(expected):
        raise RuntimeConfigurationError("behavior requires the sealed control/status/events representative model")
    for register_name, (offset, fields) in expected.items():
        register = registers[register_name]
        if register.get("offset_bytes") != offset:
            raise RuntimeConfigurationError(f"behavior fixture register {register_name} has an unexpected offset")
        actual_fields = {field.get("name"): field for field in register.get("fields", [])}
        if set(actual_fields) != set(fields):
            raise RuntimeConfigurationError(f"behavior fixture register {register_name} has unexpected fields")
        for field_name, (sw_access, hw_access, reset) in fields.items():
            field = actual_fields[field_name]
            if (
                field.get("sw_access") != sw_access
                or field.get("hw_access") != hw_access
                or field.get("reset") != reset
            ):
                raise RuntimeConfigurationError(
                    f"behavior fixture field {register_name}.{field_name} does not match sealed access/reset semantics"
                )


def _rtl_module_name(rtl: Path) -> str:
    match = re.search(r"^\s*module\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(", rtl.read_text(encoding="utf-8"), re.MULTILINE)
    if match is None:
        raise RuntimeConfigurationError(f"cannot discover top RTL module in {rtl}")
    return match.group(1)


def _behavior_testbench(module_name: str) -> str:
    """Return a deterministic, deliberately no-timescale APB testbench."""

    return f"""module address_planner_behavior_tb;
    reg         clk;
    reg         rst_n;
    reg  [31:0] p_addr;
    reg         p_sel;
    reg         p_enable;
    reg         p_write;
    reg  [31:0] p_wdata;
    wire        p_ready;
    wire [31:0] p_rdata;
    wire        p_slverr;
    wire        control_enable_rdat;
    wire [2:0]  control_mode_rdat;
    reg         status_ready_wdat;
    reg         status_ready_wena;
    wire        status_ready_rdat;
    reg  [3:0]  events_pending_wdat;
    reg         events_pending_wena;
    wire [3:0]  events_pending_rdat;

    {module_name} dut (
        .clk                 (clk),
        .rst_n               (rst_n),
        .p_addr              (p_addr),
        .p_sel               (p_sel),
        .p_enable            (p_enable),
        .p_write             (p_write),
        .p_wdata             (p_wdata),
        .p_ready             (p_ready),
        .p_rdata             (p_rdata),
        .p_slverr            (p_slverr),
        .control_enable_rdat (control_enable_rdat),
        .control_mode_rdat   (control_mode_rdat),
        .status_ready_wdat   (status_ready_wdat),
        .status_ready_wena   (status_ready_wena),
        .status_ready_rdat   (status_ready_rdat),
        .events_pending_wdat (events_pending_wdat),
        .events_pending_wena (events_pending_wena),
        .events_pending_rdat (events_pending_rdat)
    );

    always #5 clk = ~clk;

    task automatic apb_write(input [31:0] addr, input [31:0] data);
        begin
            @(negedge clk);
            p_addr = addr;
            p_wdata = data;
            p_sel = 1'b1;
            p_enable = 1'b0;
            p_write = 1'b1;
            @(negedge clk);
            p_enable = 1'b1;
            @(posedge clk);
            #1;
            @(negedge clk);
            p_sel = 1'b0;
            p_enable = 1'b0;
            p_write = 1'b0;
        end
    endtask

    task automatic expect_read(input [31:0] addr, input [31:0] expected, input [8*48-1:0] label);
        begin
            @(negedge clk);
            p_addr = addr;
            p_sel = 1'b1;
            p_enable = 1'b0;
            p_write = 1'b0;
            @(negedge clk);
            p_enable = 1'b1;
            @(posedge clk);
            #1;
            if (p_rdata !== expected) begin
                $display("OBSERVATION FAIL %0s expected=0x%08x got=0x%08x", label, expected, p_rdata);
                $fatal(1);
            end
            $display("OBSERVATION PASS %0s value=0x%08x", label, p_rdata);
            @(negedge clk);
            p_sel = 1'b0;
            p_enable = 1'b0;
        end
    endtask

    initial begin
        clk = 1'b0;
        rst_n = 1'b0;
        p_addr = 32'h0;
        p_sel = 1'b0;
        p_enable = 1'b0;
        p_write = 1'b0;
        p_wdata = 32'h0;
        status_ready_wdat = 1'b0;
        status_ready_wena = 1'b0;
        events_pending_wdat = 4'h0;
        events_pending_wena = 1'b0;
        repeat (2) @(posedge clk);
        @(negedge clk);
        rst_n = 1'b1;

        expect_read(32'h0, 32'h00000021, "reset-control-offset-0");
        expect_read(32'h4, 32'h00000000, "reset-status-offset-4");
        expect_read(32'h8, 32'h0000000a, "reset-events-offset-8");

        apb_write(32'h0, 32'h00000031);
        expect_read(32'h0, 32'h00000031, "software-rw-control");

        apb_write(32'h4, 32'h00000001);
        expect_read(32'h4, 32'h00000000, "software-write-rejected-for-ro-status");
        @(negedge clk);
        status_ready_wdat = 1'b1;
        status_ready_wena = 1'b1;
        @(posedge clk);
        #1;
        @(negedge clk);
        status_ready_wena = 1'b0;
        expect_read(32'h4, 32'h00000001, "hardware-update-and-readback-for-ro-status");

        apb_write(32'h8, 32'h00000002);
        expect_read(32'h8, 32'h00000008, "w1c-events-0xa-write-0x2");
        $display("OBSERVATION PASS register-behavior-complete");
        $finish;
    end
endmodule
"""


def behavior_rtl(manifest: Path, tool: str) -> dict[str, Any]:
    """Compile and execute the sealed representative APB register behavior test."""

    inventory(manifest)
    manifest_path = manifest.resolve()
    raw = json.loads(manifest_path.read_text(encoding="utf-8"))
    output_root = _manifest_relative_path(raw["output_root"], manifest_path.parent, "output_root")
    model_path = Path(raw["model"].get("path", ""))
    if not model_path.is_file() or _sha256(model_path) != raw["model"]["sha256"]:
        raise RuntimeConfigurationError("behavior model path is missing or does not match manifest SHA-256")
    _representative_behavior_spec(model_path)
    filelists = [record for record in raw["auxiliary_artifacts"] if record["class"] == "filelist"]
    if len(filelists) != 1:
        raise RuntimeConfigurationError("manifest must contain exactly one complete RTL filelist")
    filelist = _manifest_relative_path(filelists[0]["path"], manifest_path.parent, "filelist")
    rtl_records = [record for record in raw["artifacts"] if record["class"] == "register_rtl"]
    if len(rtl_records) != 1:
        raise RuntimeConfigurationError("manifest must contain exactly one register_rtl artifact")
    rtl_path = _manifest_relative_path(rtl_records[0]["path"], manifest_path.parent, "register_rtl")
    executable = shutil.which(tool)
    if executable is None:
        raise RuntimeConfigurationError(f"requested behavior tool is not available on PATH: {tool}")
    tool_path = Path(executable).resolve()
    try:
        version = subprocess.check_output(
            [str(tool_path), "--version"], text=True, stderr=subprocess.STDOUT, timeout=10
        ).splitlines()[0]
    except (OSError, subprocess.CalledProcessError, subprocess.TimeoutExpired, IndexError) as error:
        raise RuntimeConfigurationError(f"cannot determine {tool_path} version: {error}") from error

    verification_root = output_root / "verification"
    testbench_path = verification_root / "register_behavior_tb.v"
    testbench_path.parent.mkdir(parents=True, exist_ok=True)
    testbench_path.write_text(_behavior_testbench(_rtl_module_name(rtl_path)), encoding="utf-8")
    work_root = verification_root / f"register_behavior_{tool_path.name}.obj"
    shutil.rmtree(work_root, ignore_errors=True)
    compile_argv = [
        str(tool_path),
        "--binary",
        "--timing",
        "--top-module",
        "address_planner_behavior_tb",
        "-f",
        str(filelist),
        str(testbench_path),
        "--Mdir",
        str(work_root),
    ]
    log_path = verification_root / f"register_behavior_{tool_path.name}.log"
    temporary_name: str | None = None
    run_argv: list[str] = []
    compile_exit: int
    run_exit: int | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", dir=log_path.parent, prefix=f".{log_path.name}.", delete=False
        ) as handle:
            temporary_name = handle.name
            handle.write(json.dumps({"compile_argv": compile_argv, "tool_version": version}, sort_keys=True) + "\n")
            handle.write("=== COMPILE ===\n")
            handle.flush()
            compiled = subprocess.run(
                compile_argv, stdout=handle, stderr=subprocess.STDOUT, text=True, check=False
            )
            compile_exit = compiled.returncode
            if compile_exit == 0:
                behavior_binary = work_root / "Vaddress_planner_behavior_tb"
                run_argv = [str(behavior_binary)]
                handle.write(json.dumps({"run_argv": run_argv}, sort_keys=True) + "\n")
                handle.write("=== RUN ===\n")
                handle.flush()
                completed = subprocess.run(
                    run_argv, stdout=handle, stderr=subprocess.STDOUT, text=True, check=False
                )
                run_exit = completed.returncode
        Path(temporary_name).replace(log_path)
        temporary_name = None
    finally:
        if temporary_name is not None:
            Path(temporary_name).unlink(missing_ok=True)
    if not log_path.is_file() or log_path.stat().st_size <= 0:
        raise RuntimeConfigurationError(f"behavior log was not created: {log_path}")

    payload: dict[str, Any] = {
        "manifest": str(manifest_path),
        "tool": str(tool_path),
        "version": version,
        "compile_argv": compile_argv,
        "compile_exit_code": compile_exit,
        "run_argv": run_argv,
        "run_exit_code": run_exit,
        "log": str(log_path),
        "log_sha256": _sha256(log_path),
    }
    if compile_exit != 0 or run_exit != 0:
        return payload

    record = {
        "kind": "register_behavior",
        "tool": {"requested": tool, "path": str(tool_path), "version": version},
        "argv": compile_argv,
        "exit_code": compile_exit,
        "run": {"argv": run_argv, "exit_code": run_exit},
        "inputs": {
            "model_sha256": raw["model"]["sha256"],
            "required_artifact_sha256": _required_artifact_hashes(raw["artifacts"]),
        },
        "supporting_artifacts": [
            _artifact_record("testbench", testbench_path, manifest_path.parent),
            _artifact_record("filelist", filelist, manifest_path.parent),
        ],
        "log": {
            "path": _manifest_relative(log_path, manifest_path.parent),
            "size_bytes": log_path.stat().st_size,
            "sha256": _sha256(log_path),
        },
    }
    raw["verification_records"] = [
        prior for prior in raw["verification_records"] if prior["kind"] != record["kind"]
    ] + [record]
    _write_json_atomically(manifest_path, raw)
    payload["manifest_sha256"] = _sha256(manifest_path)
    return payload


def _capability_file(path: Path, label: str) -> dict[str, Any]:
    if not path.is_file() or path.stat().st_size <= 0:
        raise RuntimeConfigurationError(f"capabilities requires non-empty {label}: {path}")
    return {"label": label, "path": str(path.resolve()), "sha256": _sha256(path), "size_bytes": path.stat().st_size}


def _capability_command(argv: list[str], output_dir: Path, label: str) -> dict[str, Any]:
    log = output_dir / f"{label}.log"
    completed = subprocess.run(argv, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, check=False)
    log.write_text(completed.stdout, encoding="utf-8")
    if completed.returncode:
        raise RuntimeConfigurationError(f"capability command {label} failed with exit {completed.returncode}: {completed.stdout}")
    return {"kind": "command", "argv": argv, "exit_code": completed.returncode, "log": _capability_file(log, f"{label}_log")}


def _capability_model(name: str, interface: str) -> dict[str, Any]:
    return {"schema_version": 1, "model_id": name, "name": name, "description": "sealed capability probe", "size_bytes": 256, "bus_width": 32, "software_interface": interface, "registers": [{"name": "control", "offset_bytes": 0, "width_bits": 32, "fields": [{"name": "enable", "lsb": 0, "width_bits": 1, "sw_access": "RW", "hw_access": "RO", "reset": 0}]}]}


def _bus_protocol_evidence(bus_id: str, interface: str, generated_manifest: Path, output_dir: Path) -> dict[str, Any]:
    """Assert protocol-specific generated RTL ports and publish hash-bound evidence."""
    raw = json.loads(generated_manifest.read_text(encoding="utf-8"))
    rtl_record = next(item for item in raw["artifacts"] if item["class"] == "register_rtl")
    rtl = _manifest_relative_path(rtl_record["path"], generated_manifest.parent, "register_rtl")
    text = rtl.read_text(encoding="utf-8")
    def has(name: str, width: int | None = None) -> bool:
        match = re.search(rf"\b(?:input|output)\s*(?:reg\s+)?(?:\[\s*(\d+)\s*:\s*0\s*\]\s*)?{re.escape(name)}\b", text)
        return match is not None and (width is None or (int(match.group(1)) + 1 if match.group(1) is not None else 1) == width)
    apb_ports = ("p_addr", "p_sel", "p_enable", "p_write", "p_wdata", "p_ready", "p_rdata", "p_slverr")
    vr_ports = ("rreq_addr", "rreq_vld", "rreq_rdy", "rack_data", "rack_vld", "rack_rdy", "wreq_addr", "wreq_vld", "wreq_rdy", "wreq_data")
    if interface == "apb":
        checks = {"base_apb_ports": all(has(name) for name in apb_ports), "no_p_strb": not has("p_strb"), "no_p_prot": not has("p_prot")}
    elif interface == "apb4":
        checks = {"base_apb_ports": all(has(name) for name in apb_ports), "p_strb_4_bits": has("p_strb", 4), "p_prot_3_bits": has("p_prot", 3)}
    elif interface == "vr":
        checks = {"valid_ready_ports": all(has(name) for name in vr_ports), "no_apb_ports": not any(has(name) for name in apb_ports + ("p_strb", "p_prot"))}
    else:
        raise RuntimeConfigurationError(f"unsupported sealed bus interface {interface!r}")
    if not all(checks.values()):
        raise RuntimeConfigurationError(f"bus protocol evidence failed for {bus_id}: " + ", ".join(key for key, value in checks.items() if not value))
    report = output_dir / f"bus_{bus_id}_protocol.json"
    _write_json_atomically(report, {"schema_version": 1, "bus_id": bus_id, "software_interface": interface, "checks": checks, "rtl": _capability_file(rtl, f"bus_{bus_id}_rtl")})
    return _capability_file(report, f"bus_{bus_id}_protocol")


def _advanced_capability_bank(spec: dict[str, Any]) -> Any:
    """Exercise all sealed advanced constructs in one real RegSpace generation."""
    from . import (ExternalField, Field, InterruptRegister, LockField, Magic, Normal, RegSpace,
                   Register, IntrMask, W1PField)
    constructs = {item["id"]: item for item in spec["constructs"]}
    bank = RegSpace("advanced_capabilities", 4096, software_interface="apb")
    arrays = constructs["register_arrays"]
    for index in range(arrays["count"]):
        reg = Register(f"array_{index}")
        reg.add(Field("enable", 1), 0)
        bank.add(reg, arrays["base_offset_bytes"] + index * arrays["stride_bytes"])
    intr = constructs["interrupt_registers"]
    # Avoid a name ending in a character from ``_raw_status``: the legacy RTL
    # backend uses str.rstrip for that suffix when naming interrupt set/clear ports.
    intr_reg = InterruptRegister("irq0", reg_type=IntrMask)
    intr_reg.add_intr_field("irq", intr["field_width_bits"])
    bank.add_intr(intr_reg, intr["base_offset_bytes"])
    magic = constructs["magic_lock_protection"]
    magic_reg = Register("magic", reg_type=Magic)
    magic_reg.add_magic(password=magic["magic_password"])
    lock_reg = Register("lock")
    lock_reg.add(LockField("guard"), 0)
    protected = Register("protected")
    protected.add(Field("data", 8), 0)
    bank.add(magic_reg, magic["magic_offset_bytes"])
    bank.add(lock_reg, magic["lock_offset_bytes"])
    bank.add(protected, magic["protected_offset_bytes"], magic_list=["magic"], lock_list=["lock.guard"])
    parity = constructs["parity_generation"]
    parity_reg = Register("parity", parity=True)
    parity_reg.add(Field("data", 8), 0)
    bank.add(parity_reg, parity["register_offset_bytes"])
    external = constructs["external_fields"]
    external_reg = Register("external")
    from .GlobalValues import get_field_access_by_value
    external_reg.add(ExternalField("status", 1, get_field_access_by_value(external["sw_access"]), get_field_access_by_value(external["hw_access"])), 0)
    bank.add(external_reg, external["register_offset_bytes"])
    pulse = constructs["pulse_fields"]
    pulse_reg = Register("pulse")
    pulse_reg.add(W1PField("kick", 1), 0)
    bank.add(pulse_reg, pulse["register_offset_bytes"])
    resets = constructs["multiple_reset_domains"]
    for index, (offset, domain) in enumerate(zip(resets["register_offsets_bytes"], resets["reset_domains"])):
        reset_reg = Register(f"reset_{index}", rst_domain=domain)
        reset_reg.add(Field("value", 1), 0)
        bank.add(reset_reg, offset)
    return bank


def _validate_capability_payload(payload: dict[str, Any], required: list[str], optional: list[str]) -> None:
    """Reject incomplete/tampered capability reports before their atomic publish."""
    if payload.get("schema_version") != 1 or not isinstance(payload.get("capabilities"), list):
        raise RuntimeConfigurationError("capability report schema is invalid")
    rows = {row.get("id"): row for row in payload["capabilities"] if isinstance(row, dict)}
    if len(rows) != len(payload["capabilities"]) or set(rows) != set(required) | set(optional):
        raise RuntimeConfigurationError("capability report capability ID set is incomplete or has unknown IDs")
    for capability_id in required:
        if rows[capability_id].get("status") != "pass" or not rows[capability_id].get("evidence"):
            raise RuntimeConfigurationError(f"capability report has no passing executable evidence for {capability_id}")
    for capability_id in optional:
        if rows[capability_id].get("status") != "observed_nonmandatory" or not rows[capability_id].get("reason"):
            raise RuntimeConfigurationError(f"capability report misclassifies observed nonmandatory {capability_id}")
    paths: list[str] = []
    def collect(value: Any) -> None:
        if isinstance(value, dict):
            for key, item in value.items():
                if key == "path" and isinstance(item, str):
                    paths.append(item)
                collect(item)
        elif isinstance(value, list):
            for item in value:
                collect(item)
    collect(payload)
    missing = [path for path in paths if not Path(path).exists()]
    if missing:
        raise RuntimeConfigurationError("capability report references missing evidence: " + ", ".join(missing))


def _capability_owned_path(root: Path, path: Path, prefix: str) -> None:
    """Reject cleanup targets that are not a direct, non-symlink owned child of ``root``."""

    try:
        relative = path.relative_to(root)
    except ValueError as error:
        raise RuntimeConfigurationError(f"capability publication target escaped its root: {path}") from error
    if (
        relative.parent != Path(".")
        or not path.name.startswith(prefix)
        or path.is_symlink()
    ):
        raise RuntimeConfigurationError(f"refusing unsafe capability publication target: {path}")


def _capability_rebase_string(value: str, stage: Path, final: Path) -> str:
    """Rebase only the exact owned stage prefix; external fixture and tool paths are untouched."""

    source = str(stage)
    if source not in value:
        return value
    return value.replace(source, str(final))


def _rebase_capability_value(value: Any, stage: Path, final: Path) -> Any:
    if isinstance(value, str):
        return _capability_rebase_string(value, stage, final)
    if isinstance(value, list):
        return [_rebase_capability_value(item, stage, final) for item in value]
    if isinstance(value, dict):
        return {key: _rebase_capability_value(item, stage, final) for key, item in value.items()}
    return value


def _physical_capability_path(path: Path, stage: Path, final: Path) -> Path:
    """Map a final logical path back into its staged physical tree for hash refreshes."""

    try:
        return stage / path.relative_to(final)
    except ValueError:
        return path


def _refresh_capability_evidence(value: Any, stage: Path, final: Path) -> None:
    """Refresh hashes/sizes after textual path rebasing changed generated evidence files."""

    if isinstance(value, dict):
        path_value = value.get("path")
        if (
            isinstance(path_value, str)
            and isinstance(value.get("sha256"), str)
            and isinstance(value.get("size_bytes"), int)
        ):
            physical = _physical_capability_path(Path(path_value), stage, final)
            if not physical.is_file():
                raise RuntimeConfigurationError(
                    f"capability evidence disappeared while refreshing publication paths: {physical}"
                )
            value["size_bytes"] = physical.stat().st_size
            value["sha256"] = _sha256(physical)
        for item in value.values():
            _refresh_capability_evidence(item, stage, final)
    elif isinstance(value, list):
        for item in value:
            _refresh_capability_evidence(item, stage, final)


def _refresh_rebased_capability_manifests(stage: Path) -> None:
    """Re-hash generated records after their output files were rebased to final paths."""

    for manifest_path in sorted(stage.rglob("manifest.json")):
        try:
            raw = json.loads(manifest_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            raise RuntimeConfigurationError(
                f"cannot refresh staged capability manifest {manifest_path}: {error}"
            ) from error
        if not isinstance(raw, dict):
            raise RuntimeConfigurationError(f"staged capability manifest is not an object: {manifest_path}")
        for collection in ("artifacts", "auxiliary_artifacts"):
            records = raw.get(collection)
            if not isinstance(records, list):
                raise RuntimeConfigurationError(
                    f"staged capability manifest has invalid {collection}: {manifest_path}"
                )
            for index, record in enumerate(records):
                if not isinstance(record, dict):
                    raise RuntimeConfigurationError(
                        f"staged capability manifest has invalid {collection}[{index}]: {manifest_path}"
                    )
                artifact = _manifest_relative_path(
                    record.get("path"), manifest_path.parent, f"{collection}[{index}]"
                )
                record["size_bytes"] = artifact.stat().st_size
                record["sha256"] = _sha256(artifact)
        _write_json_atomically(manifest_path, raw)


def _refresh_rebased_capability_json_records(stage: Path, final: Path) -> None:
    """Refresh embedded absolute-path evidence records in generated JSON reports."""

    def refresh(value: Any) -> None:
        if isinstance(value, dict):
            path_value = value.get("path")
            if (
                isinstance(path_value, str)
                and Path(path_value).is_absolute()
                and isinstance(value.get("sha256"), str)
                and isinstance(value.get("size_bytes"), int)
            ):
                physical = _physical_capability_path(Path(path_value), stage, final)
                if physical != Path(path_value):
                    if not physical.is_file():
                        raise RuntimeConfigurationError(
                            f"rebased JSON evidence is missing from stage: {physical}"
                        )
                    value["size_bytes"] = physical.stat().st_size
                    value["sha256"] = _sha256(physical)
            for item in value.values():
                refresh(item)
        elif isinstance(value, list):
            for item in value:
                refresh(item)

    for json_path in sorted(stage.rglob("*.json")):
        try:
            raw = json.loads(json_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        refresh(raw)
        _write_json_atomically(json_path, raw)


def _refresh_rebased_capability_command_logs(stage: Path, final: Path) -> None:
    """Refresh backend-emitted JSON summary lines after their nested output hashes changed."""

    for log_path in sorted(stage.glob("*.log")):
        try:
            lines = log_path.read_text(encoding="utf-8").splitlines()
        except OSError as error:
            raise RuntimeConfigurationError(f"cannot refresh capability command log {log_path}: {error}") from error
        changed = False
        for index, line in enumerate(lines):
            try:
                summary = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not isinstance(summary, dict) or not isinstance(summary.get("sha256"), str):
                continue
            target_value = summary.get("manifest", summary.get("report"))
            if not isinstance(target_value, str):
                continue
            target = _physical_capability_path(Path(target_value), stage, final)
            if not target.is_file():
                continue
            summary["sha256"] = _sha256(target)
            lines[index] = json.dumps(summary, sort_keys=True)
            changed = True
        if changed:
            log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _validate_capability_stage_payload(
    payload: dict[str, Any], required: list[str], optional: list[str], stage: Path, final: Path
) -> None:
    """Validate final-path payload against the physical staged evidence before publication."""

    staged_payload = _rebase_capability_value(payload, final, stage)
    _validate_capability_payload(staged_payload, required, optional)


def _validate_capability_final_payload(
    payload: dict[str, Any], required: list[str], optional: list[str]
) -> None:
    """Final-path validation seam, kept separate from staged validation for rollback tests."""

    _validate_capability_payload(payload, required, optional)


def _validate_capability_targets(
    secondary_output_dir: Path, capability_report: Path
) -> tuple[Path, Path, Path]:
    """Return an owned evidence final and report target without accepting symlinked roots."""

    _reject_symlinked_target(secondary_output_dir, "secondary_output_dir")
    _reject_symlinked_target(capability_report, "capability_report")
    root = secondary_output_dir.expanduser().resolve()
    report = capability_report.expanduser().resolve()
    if root == root.parent or root == Path("/") or root.name in {"", ".", ".."}:
        raise RuntimeConfigurationError("refusing unsafe secondary output directory")
    if not root.exists():
        root.mkdir(parents=True, exist_ok=True)
        _reject_symlinked_target(root, "secondary_output_dir")
    if not root.is_dir() or root.is_symlink():
        raise RuntimeConfigurationError(f"secondary_output_dir must be a real directory: {root}")
    if report.parent.exists() and not report.parent.is_dir():
        raise RuntimeConfigurationError(f"capability report parent is not a directory: {report.parent}")
    report.parent.mkdir(parents=True, exist_ok=True)
    _reject_symlinked_target(report.parent, "capability report parent")
    if report.exists() and (not report.is_file() or report.is_symlink()):
        raise RuntimeConfigurationError(f"capability report must be a regular file when it exists: {report}")
    final = root / "evidence_v1"
    if final.exists() and (not final.is_dir() or final.is_symlink()):
        raise RuntimeConfigurationError(f"capability evidence target must be a real directory: {final}")
    try:
        report.relative_to(final)
    except ValueError:
        pass
    else:
        raise RuntimeConfigurationError("capability report must not be inside the evidence tree")
    return root, final, report


def _rollback_capability_publication(
    *,
    root: Path,
    final: Path,
    report: Path,
    stage: Path,
    tree_backup: Path | None,
    report_backup: Path | None,
    pending_report: Path | None,
    published_tree: bool,
    published_report: bool,
) -> list[Exception]:
    """Reverse an A08 exchange without deleting old or newly generated evidence."""

    errors: list[Exception] = []
    failed_tree = root / f".{final.name}.failed-{stage.name}"
    failed_report = report.parent / f".{report.name}.failed-{stage.name}"
    if published_report and report.exists():
        try:
            _publish_replace(report, failed_report)
        except OSError as error:
            errors.append(error)
    if published_tree and final.exists():
        try:
            _publish_replace(final, stage)
        except OSError as error:
            errors.append(error)
    if report_backup is not None and report_backup.exists():
        try:
            _publish_replace(report_backup, report)
        except OSError as error:
            errors.append(error)
    if tree_backup is not None and tree_backup.exists():
        try:
            _publish_replace(tree_backup, final)
        except OSError as error:
            errors.append(error)
    if pending_report is not None and pending_report.exists():
        try:
            _publish_replace(pending_report, failed_report)
        except OSError as error:
            errors.append(error)
    # Keep a failed new tree only in the exact owned staging name.  ``failed_tree`` exists
    # solely to make a name collision explicit rather than overwriting an unknown entry.
    if failed_tree.exists():
        errors.append(RuntimeConfigurationError(f"owned capability failure target already exists: {failed_tree}"))
    return errors


def _cleanup_capability_publication(
    root: Path, tree_backup: Path | None, report: Path, report_backup: Path | None
) -> None:
    """Remove only verified owned backups after final evidence and report validation."""

    if tree_backup is not None and tree_backup.exists():
        _capability_owned_path(root, tree_backup, ".evidence_v1.backup-")
        if not tree_backup.is_dir():
            raise RuntimeConfigurationError(f"capability tree backup is not a directory: {tree_backup}")
        shutil.rmtree(tree_backup)
    if report_backup is not None and report_backup.exists():
        if report_backup.parent != report.parent or not report_backup.name.startswith(f".{report.name}.backup-"):
            raise RuntimeConfigurationError(f"refusing unsafe capability report backup: {report_backup}")
        if report_backup.is_symlink() or not report_backup.is_file():
            raise RuntimeConfigurationError(f"capability report backup is not a regular file: {report_backup}")
        report_backup.unlink()


def capabilities(manifest: Path, baseline_contract: Path, capability_report: Path,
                 secondary_output_dir: Path, excel_input: Path, ralf_input: Path,
                 bus_models: Path, advanced_models: Path, matrix_model: Path,
                 dv_log_input: Path) -> dict[str, Any]:
    """Execute retained backend probes, then transactionally exchange evidence and report."""
    inventory(manifest)
    manifest_path = manifest.resolve()
    try:
        contract = json.loads(baseline_contract.read_text(encoding="utf-8"))
        buses = json.loads(bus_models.read_text(encoding="utf-8"))
        advanced = json.loads(advanced_models.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeConfigurationError(f"cannot read capabilities fixture: {error}") from error
    required = [entry["id"] for entry in contract["capabilities"] if entry["disposition"] in {"retain", "repair"}]
    optional = [entry["id"] for entry in contract["capabilities"] if entry["disposition"] == "observed_nonmandatory"]
    fixture_paths = {"manifest": manifest_path, "baseline_contract": baseline_contract.resolve(), "excel_input": excel_input.resolve(), "ralf_input": ralf_input.resolve(), "bus_models": bus_models.resolve(), "advanced_models": advanced_models.resolve(), "matrix_model": matrix_model.resolve(), "dv_log_input": dv_log_input.resolve()}
    fixture_evidence = [_capability_file(path, label) for label, path in fixture_paths.items()]
    before_hashes = {entry["label"]: entry["sha256"] for entry in fixture_evidence}
    acceptance_dir = manifest_path.parent
    preflight = _capability_file(acceptance_dir / "preflight.json", "A01_preflight")
    unit = _capability_file(acceptance_dir / "unit_tests.xml", "A02_unit_tests")
    if any(int(node.get(key, 0)) for node in __import__("xml.etree.ElementTree", fromlist=["parse"]).parse(unit["path"]).getroot().iter("testsuite") for key in ("failures", "errors", "skipped")):
        raise RuntimeConfigurationError("A02 JUnit evidence is not a clean pass")
    raw_manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    verification = {item["kind"]: item for item in raw_manifest["verification_records"]}
    if set(("strict_compile", "register_behavior")) - set(verification):
        raise RuntimeConfigurationError("A05/A06 verification records are required before capabilities")
    consistency_path = _manifest_relative_path(raw_manifest["output_root"], acceptance_dir, "output_root") / "verification" / "consistency_report.json"
    consistency_evidence = _capability_file(consistency_path, "A07_consistency")
    root, final, report_path = _validate_capability_targets(secondary_output_dir, capability_report)
    stage = Path(tempfile.mkdtemp(prefix=".evidence_v1.stage-", dir=root))
    tree_backup: Path | None = None
    report_backup: Path | None = None
    pending_report: Path | None = None
    records: dict[str, list[dict[str, Any]]] = {}
    published_tree = False
    published_report = False
    committed_and_validated = False
    # JSON backends allocate presentation keys through this process-global counter.  Scope it
    # to this complete A08 publication so a rerun produces the same evidence tree without
    # leaking a counter mutation back to the caller.
    from . import GlobalValues

    prior_json_key = GlobalValues.key
    GlobalValues.key = 0
    try:
        # Bus backends are generated by the canonical CLI path, once per sealed interface.
        for bus in buses["models"]:
            model_path = stage / f"{bus['id']}.json"
            model_path.write_text(json.dumps(_capability_model(f"bus_{bus['id']}", bus["software_interface"]), indent=2, sort_keys=True) + "\n", encoding="utf-8")
            out = stage / "bus" / bus["id"]
            out.mkdir(parents=True)
            generated_manifest = out / "manifest.json"
            command_evidence = _capability_command([sys.executable, "-m", "address_planner.selftest", "generate", "--model-definition", str(model_path), "--output-dir", str(out / "generated"), "--manifest", str(generated_manifest)], stage, f"bus_{bus['id']}")
            records[f"bus_{bus['id']}"] = [command_evidence, _capability_file(generated_manifest, f"bus_{bus['id']}_manifest"), _bus_protocol_evidence(bus["id"], bus["software_interface"], generated_manifest, stage)]
        records["excel_cli"] = [_capability_command([sys.executable, str(resolve_address_planner_root() / "regbuilder.py"), "-e", str(excel_input.resolve()), "-o", str(stage / "excel")], stage, "excel_cli")]
        records["ralf_import"] = [_capability_command([sys.executable, "-m", "address_planner.ralf_parser.main", "--input", str(ralf_input.resolve()), "--output-dir", str(stage / "ralf"), "--report", str(stage / "ralf" / "report.json")], stage, "ralf_import")]
        from .MatrixSpace import MatrixSpace
        matrix_report = MatrixSpace.report_fixed_model(matrix_model, stage / "matrix")
        records["matrix_reports"] = [{"kind": "python_api", "call": "MatrixSpace.report_fixed_model", "artifact": _capability_file(matrix_report, "matrix_report")}]
        records["dv_log_parser_capability"] = [_capability_command([sys.executable, str(resolve_address_planner_root() / "dv_env" / "dv_logparser.py"), "--simv-log", str(dv_log_input.resolve()), "--report", str(stage / "dv_log.json")], stage, "dv_log_parser")]
        bank = _advanced_capability_bank(advanced)
        bank.generate(str(stage / "advanced"), report_dv=True)
        advanced_root = stage / "advanced" / "advanced_capabilities"
        dv_required = [
            advanced_root / "dv" / "tb.sv",
            advanced_root / "dv" / "tb.f",
            advanced_root / "dv" / "tc" / "tc_lib.sv",
            advanced_root / "ralf" / "advanced_capabilities.ralf",
        ]
        generated_ral = advanced_root / "dv" / "ral" / "ral_top.sv"
        if generated_ral.is_file():
            dv_required.append(generated_ral)
        records["advanced"] = [{"kind": "python_api", "call": "RegSpace.generate(report_dv=True)", "artifacts": [_capability_file(item, "advanced_" + item.name) for item in dv_required]}]
        rtl = next((advanced_root / "rtl").rglob("*.v"))
        rtl_evidence = _capability_file(rtl, "advanced_rtl")
        rtl_text = rtl.read_text(encoding="utf-8")
        array = next(item for item in advanced["constructs"] if item["id"] == "register_arrays")
        construct_checks = {
            "register_arrays": all(f"array_{index}_rdat" in rtl_text and f"32'h{array['base_offset_bytes'] + index * array['stride_bytes']:x}" in rtl_text for index in range(array["count"])),
            "interrupt_registers": all(token in rtl_text for token in ("irq0_raw_status", "irq0_enable", "irq0_clear", "irq0_set", "irq0_mask")),
            "magic_lock_protection": all(token in rtl_text for token in ("magic", "lock", "protected")),
            "parity_generation": any(
                token in rtl_text
                for token in ("parity_parity_check_err", "parity_sw_check_err")
            ),
            "external_fields": "external_status_rdat" in rtl_text and "external_status_rvld" in rtl_text,
            "pulse_fields": "pulse_kick_rdat" in rtl_text and "pulse_kick_ena" in rtl_text,
            "multiple_reset_domains": "rst_a_n" in rtl_text and "rst_b_n" in rtl_text,
        }
        if not all(construct_checks.values()):
            raise RuntimeConfigurationError("advanced construct RTL evidence missing: " + ", ".join(key for key, value in construct_checks.items() if not value))
        records["advanced_constructs"] = {
            item["id"]: [{"kind": "rtl_feature_check", "passed": construct_checks[item["id"]], "fixture": _capability_file(advanced_models.resolve(), "advanced_models"), "artifact": rtl_evidence}]
            for item in advanced["constructs"]
        }
        rows: list[dict[str, Any]] = []
        common = [{"kind": "A01", "artifact": preflight}, {"kind": "A02", "artifact": unit}, {"kind": "A07", "artifact": consistency_evidence}]
        artifact_by_class = {item["class"]: _capability_file(_manifest_relative_path(item["path"], acceptance_dir, item["class"]), item["class"]) for item in raw_manifest["artifacts"]}
        verification_evidence = {kind: {"kind": kind, "exit_code": record["exit_code"], "log": _capability_file(_manifest_relative_path(record["log"]["path"], acceptance_dir, f"{kind}_log"), f"{kind}_log"), "inputs": record["inputs"]} for kind, record in verification.items()}
        mapping = {"dependency_resolution": common[:1], "register_model": common[1:], "address_space_model": common[1:], "field_access_types": [{"kind": "A06", "record": verification_evidence["register_behavior"]}], "model_validation": common[1:], "rtl_backend": [{"kind": "A05", "record": verification_evidence["strict_compile"]}], "c_header_backend": [{"kind": "artifact", "artifact": artifact_by_class["c_header"]}], "verilog_header_backend": [{"kind": "artifact", "artifact": artifact_by_class["verilog_header"]}], "ralf_backend": [{"kind": "artifact", "artifact": artifact_by_class["ralf"]}], "json_backend": [{"kind": "artifact", "artifact": artifact_by_class["json"]}], "dv_backends": records["advanced"], "bus_interfaces": [records[key] for key in sorted(records) if key.startswith("bus_")], "register_arrays": records["advanced_constructs"]["register_arrays"], "interrupt_registers": records["advanced_constructs"]["interrupt_registers"], "magic_lock_protection": records["advanced_constructs"]["magic_lock_protection"], "parity_generation": records["advanced_constructs"]["parity_generation"], "external_fields": records["advanced_constructs"]["external_fields"], "pulse_fields": records["advanced_constructs"]["pulse_fields"], "multiple_reset_domains": records["advanced_constructs"]["multiple_reset_domains"], "excel_cli": records["excel_cli"], "ralf_import": records["ralf_import"], "ralf_parser_cli": records["ralf_import"], "matrix_reports": records["matrix_reports"], "dv_log_parser_capability": records["dv_log_parser_capability"]}
        for capability_id in required:
            evidence = mapping.get(capability_id)
            if not evidence:
                raise RuntimeConfigurationError(f"no executable evidence mapping for required capability {capability_id}")
            rows.append({"id": capability_id, "status": "pass", "evidence": evidence})
        rows.extend({"id": capability_id, "status": "observed_nonmandatory", "reason": "baseline disposition is observed_nonmandatory; this command does not promote it to mandatory support"} for capability_id in optional)
        if {row["id"] for row in rows} != {entry["id"] for entry in contract["capabilities"]}:
            raise RuntimeConfigurationError("capability report does not cover the baseline capability ID set")
        after_hashes = {label: _sha256(path) for label, path in fixture_paths.items()}
        if after_hashes != before_hashes:
            raise RuntimeConfigurationError("capability execution modified an input fixture")
        payload = {"schema_version": 1, "baseline_contract": _capability_file(baseline_contract.resolve(), "baseline_contract"), "manifest": _capability_file(manifest_path, "manifest"), "fixtures": fixture_evidence, "input_hashes_before": before_hashes, "input_hashes_after": after_hashes, "secondary_artifacts": records, "capabilities": sorted(rows, key=lambda row: row["id"])}

        # All backend invocations used the physical stage.  Rebase only its owned prefix in
        # generated text/JSON/logs and in the report structure, then refresh every affected
        # nested manifest and evidence record before any final target is touched.
        _normalize_staged_output_paths(stage, final)
        _refresh_rebased_capability_manifests(stage)
        _refresh_rebased_capability_json_records(stage, final)
        # JSON reports can themselves be required generated artifacts.  Refresh manifests once
        # more after their embedded evidence records were rewritten/serialized.
        _refresh_rebased_capability_manifests(stage)
        _refresh_rebased_capability_command_logs(stage, final)
        payload = _rebase_capability_value(payload, stage, final)
        _refresh_capability_evidence(payload, stage, final)
        _validate_capability_stage_payload(payload, required, optional, stage, final)

        if final.exists():
            tree_backup = root / f".{final.name}.backup-{stage.name}"
            _publish_replace(final, tree_backup)
        if report_path.exists():
            report_backup = report_path.parent / f".{report_path.name}.backup-{stage.name}"
            _publish_replace(report_path, report_backup)
        _publish_replace(stage, final)
        published_tree = True
        # This is deliberately after the directory exchange: it proves that all final logical
        # paths in the report resolve, while rollback still has the complete old tree/report.
        _validate_capability_final_payload(payload, required, optional)
        pending_report = report_path.parent / f".{report_path.name}.pending-{stage.name}"
        _write_json_atomically(pending_report, payload)
        _publish_replace(pending_report, report_path)
        published_report = True
        stored = json.loads(report_path.read_text(encoding="utf-8"))
        _validate_capability_final_payload(stored, required, optional)
        for nested_manifest in sorted(final.rglob("manifest.json")):
            inventory(nested_manifest)
        committed_and_validated = True
        _cleanup_capability_publication(root, tree_backup, report_path, report_backup)
        return {"report": str(report_path), "sha256": _sha256(report_path), "capability_count": len(rows)}
    except Exception as error:
        if committed_and_validated:
            raise
        rollback_errors = _rollback_capability_publication(
            root=root,
            final=final,
            report=report_path,
            stage=stage,
            tree_backup=tree_backup,
            report_backup=report_backup,
            pending_report=pending_report,
            published_tree=published_tree,
            published_report=published_report,
        )
        if rollback_errors:
            raise RuntimeConfigurationError(
                "capability publication failed and rollback did not complete: "
                + "; ".join(str(rollback_error) for rollback_error in rollback_errors)
            ) from error
        raise
    finally:
        GlobalValues.key = prior_json_key


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="address-planner runtime self-checks")
    subcommands = parser.add_subparsers(dest="command", required=True)
    preflight_parser = subcommands.add_parser("preflight", help="validate roots and write a runtime report")
    preflight_parser.add_argument("--report", required=True, type=Path)
    generate_parser = subcommands.add_parser(
        "generate", help="generate a fixed-schema model and write an auditable output manifest"
    )
    generate_parser.add_argument("--model-definition", required=True, type=Path)
    generate_parser.add_argument("--output-dir", required=True, type=Path)
    generate_parser.add_argument("--manifest", required=True, type=Path)
    inventory_parser = subcommands.add_parser(
        "inventory", help="strictly validate a delivery manifest without rewriting it"
    )
    inventory_parser.add_argument("--manifest", required=True, type=Path)
    compile_parser = subcommands.add_parser(
        "compile", help="run strict RTL lint and append a replay-stable verification record"
    )
    compile_parser.add_argument("--manifest", required=True, type=Path)
    compile_parser.add_argument("--tool", required=True)
    behavior_parser = subcommands.add_parser(
        "behavior", help="compile and execute the sealed representative APB behavior test"
    )
    behavior_parser.add_argument("--manifest", required=True, type=Path)
    behavior_parser.add_argument("--tool", required=True)
    consistency_parser = subcommands.add_parser(
        "consistency", help="read-only cross-check of manifest-recorded generated representations"
    )
    consistency_parser.add_argument("--manifest", required=True, type=Path)
    capabilities_parser = subcommands.add_parser(
        "capabilities", help="execute retained backend probes and atomically publish a hash-bound capability report"
    )
    capabilities_parser.add_argument("--manifest", required=True, type=Path)
    capabilities_parser.add_argument("--baseline-contract", required=True, type=Path)
    capabilities_parser.add_argument("--capability-report", required=True, type=Path)
    capabilities_parser.add_argument("--secondary-output-dir", required=True, type=Path)
    capabilities_parser.add_argument("--excel-input", required=True, type=Path)
    capabilities_parser.add_argument("--ralf-input", required=True, type=Path)
    capabilities_parser.add_argument("--bus-models", required=True, type=Path)
    capabilities_parser.add_argument("--advanced-models", required=True, type=Path)
    capabilities_parser.add_argument("--matrix-model", required=True, type=Path)
    capabilities_parser.add_argument("--dv-log-input", required=True, type=Path)
    args = parser.parse_args(argv)
    if args.command == "preflight":
        payload = preflight(args.report)
        print(json.dumps({"report": str(args.report), "sha256": payload["report_sha256"]}, sort_keys=True))
        return 0
    if args.command == "generate":
        payload = generate(args.model_definition, args.output_dir, args.manifest)
        print(json.dumps({"manifest": str(args.manifest), "sha256": payload["manifest_sha256"]}, sort_keys=True))
        return 0
    if args.command == "inventory":
        print(json.dumps(inventory(args.manifest), sort_keys=True))
        return 0
    if args.command == "compile":
        payload = compile_rtl(args.manifest, args.tool)
        print(json.dumps(payload, sort_keys=True))
        return int(payload["exit_code"])
    if args.command == "behavior":
        payload = behavior_rtl(args.manifest, args.tool)
        print(json.dumps(payload, sort_keys=True))
        if payload["compile_exit_code"] != 0:
            return int(payload["compile_exit_code"])
        return int(payload["run_exit_code"])
    if args.command == "consistency":
        print(json.dumps(consistency(args.manifest), sort_keys=True))
        return 0
    if args.command == "capabilities":
        print(json.dumps(capabilities(args.manifest, args.baseline_contract, args.capability_report,
                                      args.secondary_output_dir, args.excel_input, args.ralf_input,
                                      args.bus_models, args.advanced_models, args.matrix_model,
                                      args.dv_log_input), sort_keys=True))
        return 0
    return 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (RuntimeConfigurationError, ModelValidationError, ManifestValidationError, OSError) as error:
        print(f"address-planner selftest failed: {error}", file=sys.stderr)
        raise SystemExit(2)
