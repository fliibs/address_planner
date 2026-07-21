
"""Import a RALF address space through the package-relative parser resource."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from tkinter import TclError

from ..AddressSpace import AddressSpace


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="RALF input file")
    parser.add_argument("--output-dir", required=True, type=Path, help="isolated output directory")
    parser.add_argument("--offset", default=0, type=lambda value: int(value, 0), help="base byte offset")
    parser.add_argument("--name", default="ralf_import", help="imported address-space name")
    parser.add_argument("--report", type=Path, help="optional JSON report path")
    args = parser.parse_args(argv)

    input_path = args.input.expanduser().resolve()
    output_dir = args.output_dir.expanduser().resolve()
    report_path = (args.report or output_dir / "ralf_import_report.json").expanduser().resolve()
    try:
        root = AddressSpace(args.name, size=1 << 40, path=str(output_dir))
        imported = root.add_ralf(input_path, args.offset, args.name)
        root.generate(str(output_dir))
        payload = {
            "input": str(input_path),
            "input_sha256": _sha256(input_path),
            "name": args.name,
            "offset_bytes": args.offset,
            "imported_module": imported.module_name,
            "output_root": str(output_dir / args.name),
        }
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, ValueError, RuntimeError, KeyError, TclError) as error:
        print(f"RALF import failed: {error}", file=sys.stderr)
        return 2
    print(json.dumps({"report": str(report_path), "sha256": _sha256(report_path)}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


