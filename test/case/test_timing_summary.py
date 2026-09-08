"""Partial logs must not be mistaken for successful, complete measurements."""

import importlib.util
import json
from pathlib import Path


def test_partial_and_multiple_process_logs(tmp_path):
    script = Path(__file__).resolve().parents[2] / 'tools/summarize_addrmap_timing.py'
    spec = importlib.util.spec_from_file_location('timing_summary', script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    path = tmp_path / 'run.log'
    rows = [
        dict(pid=1, event='start', phase='script.total', depth=0),
        dict(pid=1, event='start', phase='ralf.read', depth=1, detail='a.ralf'),
        dict(pid=1, event='end', phase='ralf.read', depth=1, wall_s=2, status='ok'),
        dict(pid=2, event='end', phase='script.total', depth=0, wall_s=3, status='error'),
        dict(pid=2, event='summary', phase='script.total', self_wall_s=3),
    ]
    path.write_text('ordinary log\n' + ''.join(module.PREFIX+json.dumps(row)+'\n' for row in rows) + module.PREFIX+'{"event":')
    result = module.summarize(path, top=1)
    first, second = result['processes']
    assert result['malformed_records'] == 1
    assert first['script_status'] is None
    assert [r['phase'] for r in first['active_at_log_end']] == ['script.total']
    assert first['phases'] == []
    assert len(first['slowest_completed']) == 1
    assert second['script_status'] == 'error'
    assert second['phases'][0]['self_wall_s'] == 3


def test_repeated_python_file_totals(tmp_path):
    script = Path(__file__).resolve().parents[2] / 'tools/summarize_addrmap_timing.py'
    spec = importlib.util.spec_from_file_location('timing_summary', script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    path = tmp_path / 'run.log'
    rows = [dict(pid=1, event='end', phase='python.file', depth=1,
                 source='child.py', detail='child.py::regBank',
                 wall_s=total, self_wall_s=own, status='ok')
            for total, own in [(3, 1), (5, 2)]]
    path.write_text(''.join(module.PREFIX+json.dumps(row)+'\n' for row in rows))
    row = module.summarize(path)['processes'][0]['python_files'][0]
    assert row == dict(source='child.py', calls=2, errors=0, wall_s=8, self_wall_s=3, max_s=5)
