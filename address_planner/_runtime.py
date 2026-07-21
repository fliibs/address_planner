"""Explicit runtime-root validation for address-planner dependencies.

The legacy ``address_planner/uhdl`` checkout is intentionally never consulted.
Consumers must provide both project roots so an import cannot silently resolve a
different U-HDL checkout from the working directory or an ambient PYTHONPATH.
"""

from __future__ import annotations

import importlib
import os
import sys
from pathlib import Path
from types import ModuleType


class RuntimeConfigurationError(RuntimeError):
    """Raised before generation when an explicit runtime dependency is invalid."""


PACKAGE_ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = PACKAGE_ROOT.parent
LEGACY_UHDL_ROOT = PACKAGE_ROOT / "uhdl"


def _configured_directory(variable: str, expected: Path) -> Path:
    raw_value = os.environ.get(variable)
    if not raw_value:
        raise RuntimeConfigurationError(
            f"{variable} is required; set it to the canonical development root."
        )

    root = Path(raw_value).expanduser().resolve()
    if root != expected:
        raise RuntimeConfigurationError(
            f"{variable}={root} does not match the imported package root {expected}."
        )
    return root


def resolve_address_planner_root() -> Path:
    """Return the explicit root for this imported package or raise a clear error."""

    root = _configured_directory("ADDRESS_PLANNER_ROOT", PROJECT_ROOT)
    if not (root / "address_planner" / "__init__.py").is_file():
        raise RuntimeConfigurationError(
            f"ADDRESS_PLANNER_ROOT={root} lacks address_planner/__init__.py."
        )
    return root


def resolve_uhdl_root() -> Path:
    """Return the explicit canonical U-HDL root and reject the nested snapshot."""

    raw_value = os.environ.get("UHDL_ROOT")
    if not raw_value:
        raise RuntimeConfigurationError(
            "UHDL_ROOT is required; set it to the canonical U-HDL development root."
        )

    root = Path(raw_value).expanduser().resolve()
    if root == LEGACY_UHDL_ROOT or LEGACY_UHDL_ROOT in root.parents:
        raise RuntimeConfigurationError(
            "UHDL_ROOT points at address_planner/address_planner/uhdl, which is a "
            "read-only legacy snapshot and cannot be used."
        )
    if not (root / "uhdl" / "__init__.py").is_file():
        raise RuntimeConfigurationError(
            f"UHDL_ROOT={root} lacks uhdl/__init__.py."
        )
    return root


def _is_below(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
    except ValueError:
        return False
    return True


def load_canonical_uhdl() -> ModuleType:
    """Import U-HDL exclusively from ``UHDL_ROOT`` and verify module provenance."""

    resolve_address_planner_root()
    root = resolve_uhdl_root()
    existing = sys.modules.get("uhdl")
    if existing is not None:
        source = getattr(existing, "__file__", None)
        if not source or not _is_below(Path(source), root):
            raise RuntimeConfigurationError(
                "U-HDL was already imported from a non-canonical location; start a "
                "fresh interpreter with UHDL_ROOT set before importing address_planner."
            )
        return existing

    root_text = str(root)
    if root_text in sys.path:
        sys.path.remove(root_text)
    sys.path.insert(0, root_text)
    module = importlib.import_module("uhdl")
    source = getattr(module, "__file__", None)
    if not source or not _is_below(Path(source), root):
        raise RuntimeConfigurationError(
            f"canonical U-HDL import resolved outside UHDL_ROOT: {source!r}."
        )
    return module
