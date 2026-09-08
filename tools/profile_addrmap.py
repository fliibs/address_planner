#!/usr/bin/env python3
"""Run an existing map script with phase timing and optional cProfile output."""

import argparse
import cProfile
import os
from pathlib import Path
import runpy
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--profile", type=Path, help="optional cProfile .pstats path (adds overhead)")
    parser.add_argument("script", type=Path)
    parser.add_argument("script_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    script = args.script.expanduser().resolve()
    if not script.is_file():
        parser.error(f"script does not exist: {script}")
    project_root = Path(__file__).resolve().parents[1]
    os.environ["ADDRESS_PLANNER_TIMING"] = "1"
    os.environ["ADDRESS_PLANNER_ROOT"] = str(project_root)
    sys.path.insert(0, str(project_root))
    from address_planner.timing import phase

    # Match `python path/to/script.py ...`, retaining the caller's cwd.
    sys.path.insert(0, str(script.parent))
    sys.argv = [str(script), *args.script_args]
    profiler = cProfile.Profile() if args.profile else None
    if args.profile:
        args.profile = args.profile.expanduser().resolve()
        args.profile.parent.mkdir(parents=True, exist_ok=True)
    with phase("script.total", script, progress=True):
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
