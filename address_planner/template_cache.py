"""Bounded, process-local compiled templates; never cache render variables.

Each render retains a fresh Jinja environment and reads its source. Jinja's
source checksum rejects old bytecode when a template changes, even if its
mtime has not changed. Set ADDRESS_PLANNER_TEMPLATE_CACHE=0 before import to
disable the optimization for an output/performance comparison.
"""

from collections import OrderedDict
import os
from threading import Lock

from jinja2 import BytecodeCache


class MemoryBytecodeCache(BytecodeCache):
    def __init__(self, max_entries=64):
        self.max_entries = max_entries
        self._entries = OrderedDict()
        self._lock = Lock()

    def load_bytecode(self, bucket):
        with self._lock:
            data = self._entries.get(bucket.key)
            if data is not None:
                self._entries.move_to_end(bucket.key)
        if data is not None:
            bucket.bytecode_from_string(data)

    def dump_bytecode(self, bucket):
        data = bucket.bytecode_to_string()
        with self._lock:
            self._entries[bucket.key] = data
            self._entries.move_to_end(bucket.key)
            while len(self._entries) > self.max_entries:
                self._entries.popitem(last=False)


TEMPLATE_BYTECODE_CACHE = (
    None if os.environ.get("ADDRESS_PLANNER_TEMPLATE_CACHE", "1").lower()
    in ("0", "false", "no") else MemoryBytecodeCache()
)
