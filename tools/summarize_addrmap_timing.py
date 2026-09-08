#!/usr/bin/env python3
"""Summarize a timing log without loading a multi-hour build log into memory."""

import argparse
import json
from pathlib import Path

PREFIX = '[addr-planner-timing] '


def summarize(path, top=10):
    processes = {}
    malformed = 0
    with Path(path).open(encoding='utf-8', errors='replace') as stream:
        for line in stream:
            if not line.startswith(PREFIX):
                continue
            try:
                row = json.loads(line[len(PREFIX):])
            except json.JSONDecodeError:
                malformed += 1
                continue
            pid = row.get('pid')
            state = processes.setdefault(pid, {'phases': {}, 'active': {}, 'slowest': [],
                                              'script_status': None, 'python_files': {}})
            event = row.get('event')
            if event == 'summary':
                state['phases'][row['phase']] = row
            elif event == 'logging_overhead':
                state['logging_overhead'] = row
            elif event == 'start':
                state['active'][row['depth']] = row
            elif event == 'end':
                state['active'].pop(row['depth'], None)
                state['slowest'].append(row)
                state['slowest'].sort(key=lambda r: r['wall_s'], reverse=True)
                del state['slowest'][top:]
                if row['phase'] == 'script.total':
                    state['script_status'] = row['status']
                if row['phase'] in ('python.file', 'script.total'):
                    source = row.get('source') or row.get('detail', '').split('::', 1)[0]
                    if source:
                        file_row = state['python_files'].setdefault(source, {
                            'source': source, 'calls': 0, 'errors': 0,
                            'wall_s': 0.0, 'self_wall_s': 0.0, 'max_s': 0.0,
                        })
                        file_row['calls'] += 1
                        file_row['errors'] += row['status'] != 'ok'
                        file_row['wall_s'] += row['wall_s']
                        file_row['self_wall_s'] += row.get('self_wall_s', 0.0)
                        file_row['max_s'] = max(file_row['max_s'], row['wall_s'])
    result = {'malformed_records': malformed, 'processes': []}
    for pid, state in processes.items():
        result['processes'].append({
            'pid': pid, 'script_status': state['script_status'],
            'phases': sorted(state['phases'].values(), key=lambda r: -r['self_wall_s']),
            'active_at_log_end': list(state['active'].values()),
            'slowest_completed': state['slowest'],
            'python_files': sorted(state['python_files'].values(), key=lambda r: -r['self_wall_s']),
            'logging_overhead': state.get('logging_overhead'),
        })
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('log', type=Path)
    parser.add_argument('--top', type=int, default=10)
    parser.add_argument('--json', action='store_true', help='print machine-readable results')
    args = parser.parse_args()
    if args.top < 1:
        parser.error('--top must be positive')
    result = summarize(args.log, args.top)
    if args.json:
        print(json.dumps(result, indent=2, ensure_ascii=False))
        return
    if not result['processes']:
        print('No timing records found. Set ADDRESS_PLANNER_TIMING_LEVEL=2 or 3 before import.')
    for process in result['processes']:
        print(f"PID {process['pid']}  script status: {process['script_status'] or 'not recorded'}")
        print(f"{'phase':32} {'calls':>8} {'self(s)':>12} {'wall(s)':>12} {'cpu(s)':>12} {'errors':>7}")
        for row in process['phases'][:args.top]:
            print(f"{row['phase']:32} {row['calls']:8d} {row['self_wall_s']:12.3f} {row['wall_s']:12.3f} {row['cpu_s']:12.3f} {row['errors']:7d}")
        if not process['phases']:
            print('No exit summary yet; completed events below are only a partial view.')
        print('Slowest completed operations (inclusive times; do not sum):')
        for row in process['slowest_completed']:
            print(f"  {row['wall_s']:10.3f}s {row['phase']} {row.get('detail', '')} [{row['status']}]")
        if process['python_files']:
            print('Python 文件耗时（秒）：total 含下层工序，self 扣除已计时子工序；total 不可相加。')
            print(f"{'calls':>7} {'self(s)':>12} {'total(s)':>12} {'max(s)':>12} {'errors':>7}  文件")
            for row in process['python_files']:
                print(f"{row['calls']:7d} {row['self_wall_s']:12.6f} {row['wall_s']:12.6f} {row['max_s']:12.6f} {row['errors']:7d}  {row['source']}")
        for row in process['active_at_log_end']:
            print(f"  OPEN: {row['phase']} {row.get('detail', '')} (no matching end in this log)")
        overhead = process['logging_overhead']
        if overhead:
            print(f"日志写入/flush: {overhead['write_flush_wall_s']:.6f}s, {overhead['writes']} 次；总计时开销需 A/B 比较。")
    if result['malformed_records']:
        print(f"Ignored {result['malformed_records']} malformed/truncated timing record(s).")


if __name__ == '__main__':
    main()
