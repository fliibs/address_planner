#!/usr/bin/env python3
"""Reproducible RALF import scaling probe; creates synthetic inputs only."""

import argparse
import contextlib
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import time

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from address_planner import AddressSpace


def run(count, directory):
    source = directory / f"registers_{count}.ralf"
    source.write_text("block bank {\n" + "\n".join(
        f"register r{i} @{i * 4} {{ bytes 4; "
        "field value @0 { bits 32; access rw; reset 0; } }"
        for i in range(count)) + "\n}\n", encoding="utf-8")
    start = time.perf_counter()
    cpu = time.process_time()
    with open(os.devnull, "w") as sink, contextlib.redirect_stdout(sink):
        model = AddressSpace("soc", count * 4).add_ralf(source, 0)
    wall_s, cpu_s = time.perf_counter() - start, time.process_time() - cpu
    # No generated JSON sequence keys, object addresses or wall time in digest.
    semantics = [(r.module_name, r.offset, r.bit,
                  [(f.name, f.bit_offset, f.bit, f.init_value) for f in r.field_list])
                 for r in model.sub_space_list]
    assert len(semantics) == count
    return {"registers": count, "wall_s": wall_s, "cpu_s": cpu_s,
            "semantic_sha256": hashlib.sha256(json.dumps(semantics).encode()).hexdigest()}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--registers", nargs="+", type=int, default=[100, 200, 400])
    args = parser.parse_args()
    if any(count < 1 for count in args.registers):
        parser.error("register counts must be positive")
    with tempfile.TemporaryDirectory(prefix="ralf-benchmark-") as temporary:
        for count in args.registers:
            print(json.dumps(run(count, Path(temporary))), flush=True)


if __name__ == "__main__":
    main()
