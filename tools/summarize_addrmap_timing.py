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
            state = processes.setdefault(pid, {'phases': {}, 'active': {}, 'slowest': [], 'script_status': None})
            event = row.get('event')
            if event == 'summary':
                state['phases'][row['phase']] = row
            elif event == 'start':
                state['active'][row['depth']] = row
            elif event == 'end':
                state['active'].pop(row['depth'], None)
                state['slowest'].append(row)
                state['slowest'].sort(key=lambda r: r['wall_s'], reverse=True)
                del state['slowest'][top:]
                if row['phase'] == 'script.total':
                    state['script_status'] = row['status']
    result = {'malformed_records': malformed, 'processes': []}
    for pid, state in processes.items():
        result['processes'].append({
            'pid': pid, 'script_status': state['script_status'],
            'phases': sorted(state['phases'].values(), key=lambda r: -r['self_wall_s']),
            'active_at_log_end': list(state['active'].values()),
            'slowest_completed': state['slowest'],
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
        print('No timing records found. Enable ADDRESS_PLANNER_TIMING before import.')
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
        for row in process['active_at_log_end']:
            print(f"  OPEN: {row['phase']} {row.get('detail', '')} (no matching end in this log)")
    if result['malformed_records']:
        print(f"Ignored {result['malformed_records']} malformed/truncated timing record(s).")


if __name__ == '__main__':
    main()
