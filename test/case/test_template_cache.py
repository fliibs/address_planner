"""Compiled templates must retain the previous render isolation contract."""

import importlib
import os

from jinja2 import Environment, FileSystemLoader

from address_planner.template_cache import MemoryBytecodeCache


def test_render_isolation_and_source_reload(tmp_path, monkeypatch):
    module = importlib.import_module('address_planner.AddressLogicRoot')
    monkeypatch.setattr(module, 'PackageLoader', lambda *args: FileSystemLoader(tmp_path))
    monkeypatch.setattr(module, 'TEMPLATE_BYTECODE_CACHE', MemoryBytecodeCache())
    source = tmp_path / 'probe.j2'
    source.write_text('{% import "macro.j2" as m %}{{m.value()}} {{space.module_name}}')
    (tmp_path / 'macro.j2').write_text('{% macro value() %}{{head_type|default("unset")}}{% endmacro %}')
    root = module.AddressLogicRoot('one')
    assert root.report_from_template('probe.j2', {'head_type': 'c'}) == 'c one'
    root.module_name = 'two'
    assert root.report_from_template('probe.j2') == 'unset two'
    stamp = source.stat()
    source.write_text('changed {{space.module_name}}')
    os.utime(source, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
    assert root.report_from_template('probe.j2') == 'changed two'


def test_compile_once_per_source_and_bounded_cache(tmp_path):
    cache = MemoryBytecodeCache(max_entries=2)
    class CountingEnvironment(Environment):
        calls = 0
        def compile(self, *args, **kwargs):
            type(self).calls += 1
            return super().compile(*args, **kwargs)
    for i in range(3):
        (tmp_path / f'{i}.j2').write_text('{{value}}')
    def render(name):
        env = CountingEnvironment(loader=FileSystemLoader(tmp_path), bytecode_cache=cache)
        return env.get_template(name).render(value='same')
    assert render('0.j2') == render('0.j2') == 'same'
    assert CountingEnvironment.calls == 1
    render('1.j2')
    render('2.j2')
    assert len(cache._entries) == 2
    render('0.j2')
    assert CountingEnvironment.calls == 4
