#!/usr/bin/env python3
"""Run an existing map script with phase timing and optional cProfile output."""

import argparse
import cProfile
from contextlib import nullcontext
import os
from pathlib import Path
import runpy
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, help="optional cProfile .pstats path (adds overhead)")
    levels = parser.add_mutually_exclusive_group()
    levels.add_argument("--timing-level", type=int, choices=(1, 2, 3),
                        help="1=off (default), 2=coarse, 3=detailed; also accepts ADDRESS_PLANNER_TIMING_LEVEL")
    levels.add_argument("--timing-detail", choices=("off", "coarse", "detailed"),
                        help="legacy alias for timing levels 1, 2, 3")
    parser.add_argument("script", type=Path)
    parser.add_argument("script_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    script = args.script.expanduser().resolve()
    if not script.is_file():
        parser.error(f"script does not exist: {script}")
    project_root = Path(__file__).resolve().parents[1]
    level = str(args.timing_level) if args.timing_level is not None else (
        {"off": "1", "coarse": "2", "detailed": "3"}[args.timing_detail]
        if args.timing_detail is not None else os.environ.get("ADDRESS_PLANNER_TIMING_LEVEL", "1"))
    if level not in ("1", "2", "3"):
        parser.error("ADDRESS_PLANNER_TIMING_LEVEL must be 1, 2 or 3")
    os.environ["ADDRESS_PLANNER_TIMING_LEVEL"] = level
    os.environ["ADDRESS_PLANNER_TIMING"] = "0" if level == "1" else "1"
    os.environ["ADDRESS_PLANNER_TIMING_DETAIL"] = "detailed" if level == "3" else "coarse"
    os.environ["ADDRESS_PLANNER_ROOT"] = str(project_root)
    sys.path.insert(0, str(project_root))
    # In off mode, leave planner imports to the user's script so its original
    # initialization messages retain their normal order.
    source_scope = nullcontext()
    script_scope = nullcontext()
    if level != "1":
        from address_planner.timing import phase, source_context
        source_scope = source_context(script)
        script_scope = phase("script.total", script, progress=True)

    # Match `python path/to/script.py ...`, retaining the caller's cwd.
    sys.path.insert(0, str(script.parent))
    sys.argv = [str(script), *args.script_args]
    profiler = cProfile.Profile() if args.profile else None
    if args.profile:
        args.profile = args.profile.expanduser().resolve()
        args.profile.parent.mkdir(parents=True, exist_ok=True)
    with source_scope, script_scope:
        try:
            if profiler:
                profiler.enable()
            runpy.run_path(str(script), run_name="__main__")
        finally:
            if profiler:
                profiler.disable()
                profiler.dump_stats(str(args.profile))


if __name__ == "__main__":
    main()
