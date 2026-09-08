"""Opt-in, bounded phase timing for long address-map runs.

Set ADDRESS_PLANNER_TIMING_LEVEL before import: 1=off, 2=coarse, 3=detailed.
Records go to stderr and are flushed immediately. Legacy timing variables
remain supported when the level is absent.
"""

import atexit
from contextlib import contextmanager, nullcontext
from contextvars import ContextVar
from functools import wraps
from datetime import datetime, timezone
import json
import os
import sys
from itertools import count
from time import perf_counter, process_time
from time import perf_counter as _log_clock


_level = os.environ.get("ADDRESS_PLANNER_TIMING_LEVEL")
if _level is not None:
    if _level not in ("1", "2", "3"):
        raise ValueError("ADDRESS_PLANNER_TIMING_LEVEL must be 1, 2 or 3")
    ENABLED = _level != "1"
    DETAIL = "detailed" if _level == "3" else "coarse"
else:
    ENABLED = os.environ.get("ADDRESS_PLANNER_TIMING", "").lower() in ("1", "true", "yes")
    DETAIL = os.environ.get("ADDRESS_PLANNER_TIMING_DETAIL", "coarse")
_COARSE_PHASES = {"script.total", "python.file", "add_ralf", "generate", "regspace.generate"}
_stack = ContextVar("address_planner_timing_stack", default=())
_stats = {}
_source = ContextVar("address_planner_timing_source", default="")
_operation_ids = count(1)
_log_wall_s = 0.0
_log_writes = 0


def _enabled_for(name):
    if not ENABLED:
        return False
    if DETAIL == "detailed":
        return True
    if name not in _COARSE_PHASES:
        return False
    # RegSpace.generate calls the base implementation; report the enclosing
    # operation once in coarse mode, including its extra RTL/waiver work.
    return not (name == "generate" and any(
        frame["phase"] == "regspace.generate" for frame in _stack.get()))


def _write_log(text):
    global _log_wall_s, _log_writes
    start = _log_clock()
    try:
        print(text, file=sys.stderr, flush=True)
    finally:
        _log_wall_s += _log_clock() - start
        _log_writes += 1

_PHASE_LABELS = {
    "script.total": "整个生成脚本",
    "python.file": "加载并执行 Python 模型文件",
    "address.integrate": "将子模型集成到上层地址空间",
    "add_ralf": "导入 RALF（含读取、解析、构建和挂接）",
    "ralf.read": "读取 RALF 文件",
    "ralf.preprocess": "预处理 RALF 文本",
    "ralf.tcl_setup": "初始化 Tcl 并加载解析器",
    "ralf.tcl_eval": "Tcl 执行 RALF 定义",
    "ralf.select_root": "选择 RALF 根定义",
    "ralf.tcl_to_python": "Tcl 数据转换为 Python",
    "ralf.build_model": "构建完整 RALF 模型",
    "ralf.build_objects": "构建寄存器和地址树",
    "ralf.minimum_size": "整理模型地址范围和尺寸",
    "ralf.deepcopy": "RALF 构建中的对象复制",
    "ralf.attach": "挂接导入的地址树",
    "address.add.deepcopy": "添加地址空间时复制对象",
    "register.add.deepcopy": "添加寄存器时复制对象",
    "generate": "生成地址图和报告（含各输出阶段）",
    "regspace.generate": "生成寄存器产物（含各输出阶段）",
    "report_chead": "生成 C 头文件",
    "report_vhead": "生成 Verilog 头文件",
    "report_ralf": "生成 RALF 文件",
    "regspace.report_ralf": "生成寄存器 RALF 文件",
    "regspace.report_rtl": "生成寄存器 RTL",
    "regspace.report_dv": "生成 DV 产物",
    "report_json": "生成 JSON/Word 报告",
    "json.build": "构建 JSON 数据",
    "json.write": "写入 JSON 文件",
    "docx.build": "生成 Word 文档",
    "report_single_html": "生成单 HTML（含数据库和打包）",
    "report_sqlite": "生成 SQLite 数据库",
    "html.package": "压缩数据并打包 HTML",
    "template.load": "加载和编译模板",
    "template.render": "渲染模板",
}


def _emit(record):
    record = {"timestamp": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "pid": os.getpid(), **record}
    _write_log("[addr-planner-timing] " + json.dumps(record, ensure_ascii=True))


def _progress(event, name, detail, operation_id, parent_id, source, depth,
              wall=None, own=None, status="ok"):
    stamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    action = "开始" if event == "start" else ("完成" if status == "ok" else "失败")
    text = (f"[addr-planner-stage] {stamp} PID={os.getpid()} "
            f"{'  ' * depth}{action} #{operation_id} parent={parent_id} "
            f"{_PHASE_LABELS.get(name, name)} [{name}]")
    if detail:
        text += f" | 对象={detail}"
    if source:
        text += f" | 所属PY={source}"
    if wall is not None:
        text += f" | 总耗时={wall:.6f}s 自身耗时={own:.6f}s"
    _write_log(text)


@contextmanager
def _source_scope(path):
    token = _source.set(str(path))
    try:
        yield
    finally:
        _source.reset(token)


def source_context(path):
    """Identify the currently executing model Python file without tracing calls."""
    return _source_scope(path) if ENABLED else nullcontext()


@contextmanager
def _measure(phase, detail, progress):
    parents = _stack.get()
    operation_id = next(_operation_ids) if progress else None
    parent_id = next((p.get("operation_id") for p in reversed(parents)
                      if p.get("operation_id") is not None), None)
    source = _source.get()
    identity = {"operation_id": operation_id, "parent_id": parent_id, "source": source}
    frame = {"child_wall": 0.0, "operation_id": operation_id, "phase": phase}
    token = _stack.set(parents + (frame,))
    if progress:
        _emit({"event": "start", "phase": phase, "detail": str(detail),
               "depth": len(parents), "pid": os.getpid(), **identity})
        _progress("start", phase, detail, operation_id, parent_id, source, len(parents))
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
                   "self_wall_s": round(own, 6), **identity})
            _progress("end", phase, detail, operation_id, parent_id, source,
                      len(parents), wall, own, status)


def phase(name, detail="", *, progress=False):
    """Time a fixed phase name; per-object details are never kept in memory."""
    return _measure(name, detail, progress) if _enabled_for(name) else nullcontext()


def timed(name, *, progress=False, detail=None):
    """Decorate a phase, bypassing instrumentation entirely when disabled."""
    def decorate(func):
        @wraps(func)
        def wrapped(*args, **kwargs):
            if not _enabled_for(name):
                return func(*args, **kwargs)
            description = (detail(*args, **kwargs) if detail is not None else
                           getattr(args[0], "module_name", "") if args else "")
            with phase(name, description, progress=progress):
                return func(*args, **kwargs)
        return wrapped
    return decorate


def print_summary():
    """Print inclusive and self times; inclusive rows must not be summed."""
    rows = sorted(_stats.items(), key=lambda item: -item[1]["self_wall_s"])
    for name, row in rows:
        _emit({"event": "summary", "phase": name,
               **{key: round(value, 6) if isinstance(value, float) else value
                  for key, value in row.items()}})
    if not rows:
        return
    lines = [f"\n[addr-planner-time-summary] PID {os.getpid()} 耗时汇总（单位：秒）"]
    if "script.total" in _stats:
        lines.append(f"整个脚本累计耗时：{_stats['script.total']['wall_s']:.6f} 秒")
    lines.extend([
        "按 self(s) 从大到小排序，用于找热点。",
        "self(s)=自身耗时；total(s)=含子阶段的累计耗时；max(s)=单次最大耗时。",
        "父子阶段有重叠，不能将 total(s) 列相加；细小耗时直接显示小数，不使用科学计数法。",
        f"{'phase':32} {'calls':>7} {'self(s)':>12} {'total(s)':>12} {'max(s)':>12} {'errors':>6}  阶段含义",
    ])
    for name, row in rows:
        lines.append(
            f"{name:32} {row['calls']:7d} {row['self_wall_s']:12.6f} "
            f"{row['wall_s']:12.6f} {row['max_s']:12.6f} {row['errors']:6d}  "
            + _PHASE_LABELS.get(name, name)
        )
    _write_log('\n'.join(lines))
    io_wall, writes = _log_wall_s, _log_writes
    _emit({"event": "logging_overhead", "detail": DETAIL,
           "write_flush_wall_s": round(io_wall, 6), "writes": writes})
    _write_log(f"日志写入/flush 截至此处累计：{io_wall:.6f} 秒，共 {writes} 次；"
               "不含格式化和计时记账，总开销以关闭/开启计时的 A/B 运行比较为准。")


if ENABLED:
    atexit.register(print_summary)
