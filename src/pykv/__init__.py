"""PyKV -- an educational key-value store built from scratch in Python.

A key-value store is like a giant phonebook for your data. You give each
piece of information a unique name (the "key") and store some data (the
"value") next to it. Later, you can look up the data just by knowing
its name -- lightning fast!

Real-world key-value stores like Redis and Memcached power some of the
biggest websites in the world. PyKV teaches you how they work from the
inside, one piece at a time.

Quick start:
    >>> from pykv import BasicStore
    >>> store = BasicStore()
    >>> store.set("greeting", "Hello, world!")
    >>> store.get("greeting")
    'Hello, world!'

Features:
    - BasicStore: Simple get/set/delete operations
    - TTLStore: Keys that expire after a time limit
    - Namespace: Group keys with prefixes
    - AtomicCounter: Thread-safe counters
    - Persistence: Save and load from disk
    - Batch operations: Work with many keys at once
    - Pattern matching: Find keys with wildcards
"""

from pykv.batch import batch_delete, batch_exists, batch_get, batch_set
from pykv.counters import AtomicCounter
from pykv.errors import (
    KeyExpiredError,
    KeyNotFoundError,
    PersistenceError,
    PyKVError,
    SerializationError,
)
from pykv.namespace import Namespace
from pykv.patterns import count_matches, match_items, match_keys
from pykv.persistence import load_store, save_store
from pykv.store import BasicStore
from pykv.ttl import TTLStore
from pykv.types import StorableValue

__all__ = [
    "AtomicCounter",
    # Core
    "BasicStore",
    "KeyExpiredError",
    "KeyNotFoundError",
    # Features
    "Namespace",
    "PersistenceError",
    # Errors
    "PyKVError",
    "SerializationError",
    "StorableValue",
    "TTLStore",
    "batch_delete",
    "batch_exists",
    "batch_get",
    # Batch
    "batch_set",
    "count_matches",
    "load_store",
    "match_items",
    # Patterns
    "match_keys",
    # Persistence
    "save_store",
]
