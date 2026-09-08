"""Timing must be opt-in, bounded, nested correctly and exception-safe."""

import json

import pytest

from address_planner import timing


def records(capsys):
    return [json.loads(line.split("] ", 1)[1])
            for line in capsys.readouterr().err.splitlines()
            if line.startswith('[addr-planner-timing] ')]


def test_disabled_timer_is_silent_and_does_not_read_clock(monkeypatch, capsys):
    monkeypatch.setattr(timing, "ENABLED", False)
    monkeypatch.setattr(timing, "_stats", {})
    def unexpected_clock():
        raise AssertionError("disabled timing touched clock")
    monkeypatch.setattr(timing, "perf_counter", unexpected_clock)
    with timing.phase("disabled", progress=True):
        pass
    assert not timing._stats
    assert records(capsys) == []


def test_nested_times_and_exception_are_reported(monkeypatch, capsys):
    monkeypatch.setattr(timing, "ENABLED", True)
    monkeypatch.setattr(timing, "DETAIL", "detailed")
    monkeypatch.setattr(timing, "_stats", {})
    ticks = iter([0.0, 1.0, 4.0, 8.0])
    monkeypatch.setattr(timing, "perf_counter", lambda: next(ticks))
    error = ValueError("bad address")
    with pytest.raises(ValueError) as caught:
        with timing.phase("outer", "file.ralf", progress=True):
            with timing.phase("inner"):
                raise error
    assert caught.value is error
    assert timing._stack.get() == ()
    assert timing._stats["outer"]["wall_s"] == 8
    assert timing._stats["outer"]["self_wall_s"] == 5
    assert timing._stats["inner"]["wall_s"] == 3
    timing.print_summary()
    output = records(capsys)
    assert output[0]["event"] == "start"
    assert output[1]["status"] == "error"
    assert output[1]["detail"] == "file.ralf"
    assert all(row["errors"] == 1 for row in output if row["event"] == "summary")


def test_summary_does_not_grow_with_object_names(monkeypatch, capsys):
    monkeypatch.setattr(timing, "ENABLED", True)
    monkeypatch.setattr(timing, "DETAIL", "detailed")
    monkeypatch.setattr(timing, "_stats", {})
    for i in range(100):
        with timing.phase("copy", str(i)):
            pass
    assert len(timing._stats) == 1
    assert timing._stats["copy"]["calls"] == 100
    assert records(capsys) == []


def test_coarse_mode_skips_fine_clocks_and_details(monkeypatch, capsys):
    monkeypatch.setattr(timing, "ENABLED", True)
    monkeypatch.setattr(timing, "DETAIL", "coarse")
    monkeypatch.setattr(timing, "_stats", {})
    def unexpected(*args):
        raise AssertionError('fine instrumentation should be bypassed')
    monkeypatch.setattr(timing, 'perf_counter', unexpected)
    with timing.phase('template.render', progress=True):
        pass
    @timing.timed('address.integrate', progress=True, detail=unexpected)
    def call():
        return 42
    assert call() == 42
    assert not timing._stats
    assert records(capsys) == []


def test_model_python_context_and_parent_operations(tmp_path, monkeypatch, capsys):
    from address_planner.GlobalValues import import_inst
    monkeypatch.setattr(timing, "ENABLED", True)
    monkeypatch.setattr(timing, "_stats", {})
    child = tmp_path / 'child.py'
    parent = tmp_path / 'parent.py'
    child.write_text('regBank = object()\n')
    parent.write_text(
        'from address_planner import import_inst\n'
        f'regBank = import_inst({str(child)!r})\n'
    )
    with timing.source_context('soc.py'), timing.phase('script.total', 'soc.py', progress=True):
        assert import_inst(str(parent)) is not None
        assert timing._source.get() == 'soc.py'
    assert timing._source.get() == ''
    output = records(capsys)
    starts = [r for r in output if r['event'] == 'start']
    assert [r['source'] for r in starts] == ['soc.py', str(parent), str(child)]
    assert starts[1]['parent_id'] == starts[0]['operation_id']
    assert starts[2]['parent_id'] == starts[1]['operation_id']
    ends = {r['operation_id']: r for r in output if r['event'] == 'end'}
    assert set(ends) == {r['operation_id'] for r in starts}
    for start in starts:
        end = ends[start['operation_id']]
        assert end['source'] == start['source']
        assert end['wall_s'] >= end['self_wall_s'] >= 0
