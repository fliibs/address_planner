"""Opt-in, bounded phase timing for long address-map runs.

Set ADDRESS_PLANNER_TIMING=1 before import. Records go to stderr and are
flushed immediately; redirect stderr to a file to retain partial runs.
"""

import atexit
from contextlib import contextmanager, nullcontext
from contextvars import ContextVar
from functools import wraps
from datetime import datetime, timezone
import json
import os
import sys
from time import perf_counter, process_time


ENABLED = os.environ.get("ADDRESS_PLANNER_TIMING", "").lower() in ("1", "true", "yes")
_stack = ContextVar("address_planner_timing_stack", default=())
_stats = {}


def _emit(record):
    record = {"timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "pid": os.getpid(), **record}
    print("[addr-planner-timing] " + json.dumps(record, ensure_ascii=True),
          file=sys.stderr, flush=True)


@contextmanager
def _measure(phase, detail, progress):
    parents = _stack.get()
    frame = {"child_wall": 0.0}
    token = _stack.set(parents + (frame,))
    if progress:
        _emit({"event": "start", "phase": phase, "detail": str(detail),
               "depth": len(parents), "pid": os.getpid()})
    wall_start, cpu_start = perf_counter(), process_time()
    status = "ok"
    try:
        yield
    except BaseException as exc:
        if not (isinstance(exc, SystemExit) and exc.code in (None, 0)):
            status = "error"
        raise
    finally:
        wall = perf_counter() - wall_start
        cpu = process_time() - cpu_start
        own = max(0.0, wall - frame["child_wall"])
        _stack.reset(token)
        if parents:
            parents[-1]["child_wall"] += wall
        row = _stats.setdefault(phase, {"calls": 0, "errors": 0, "wall_s": 0.0,
                                       "self_wall_s": 0.0, "cpu_s": 0.0, "max_s": 0.0})
        row["calls"] += 1
        row["errors"] += status == "error"
        row["wall_s"] += wall
        row["self_wall_s"] += own
        row["cpu_s"] += cpu
        row["max_s"] = max(row["max_s"], wall)
        if progress:
            _emit({"event": "end", "phase": phase, "detail": str(detail),
                   "depth": len(parents), "pid": os.getpid(), "status": status,
                   "wall_s": round(wall, 6), "cpu_s": round(cpu, 6),
                   "self_wall_s": round(own, 6)})


def phase(name, detail="", *, progress=False):
    """Time a fixed phase name; per-object details are never kept in memory."""
    return _measure(name, detail, progress) if ENABLED else nullcontext()


def timed(name, *, progress=False):
    """Decorate a phase, bypassing instrumentation entirely when disabled."""
    def decorate(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            if not ENABLED:
                return func(*args, **kwargs)
            detail = getattr(args[0], "module_name", "") if args else ""
            with phase(name, detail, progress=progress):
                return func(*args, **kwargs)
        return wrapped
    return decorate


def print_summary():
    """Print inclusive and self times; inclusive rows must not be summed."""
    for name, row in sorted(_stats.items(), key=lambda item: -item[1]["self_wall_s"]):
        _emit({"event": "summary", "phase": name,
               **{key: round(value, 6) if isinstance(value, float) else value
                  for key, value in row.items()}})


if ENABLED:
    atexit.register(print_summary)
