"""Persistence -- save and load your store to disk.

Imagine you are working on a jigsaw puzzle. At the end of the day, you
take a photo of your progress so you can pick up where you left off
tomorrow. That is what persistence does for your key-value store -- it
saves everything to a file so nothing is lost when your program stops.

PyKV uses JSON files for storage because they are human-readable. You
could open the file in a text editor and see exactly what is stored,
like reading your own notebook.

Example:
    >>> from pykv.store import BasicStore
    >>> from pykv.persistence import save_store, load_store
    >>> store = BasicStore()
    >>> store.set("name", "Alice")
    >>> save_store(store, "my_data.json")
    >>> loaded = load_store("my_data.json")
    >>> loaded.get("name")
    'Alice'

"""

import json
from pathlib import Path

from pykv.atomic import atomic_write_text
from pykv.errors import PersistenceError
from pykv.store import BasicStore
from pykv.ttl import TTLStore
from pykv.types import StorableValue, deserialize_value, serialize_value


def save_store(store: BasicStore | TTLStore, filepath: str | Path) -> None:
    """Save all data from a store to a JSON file on disk.

    Like writing everything from your notebook into a save file.
    If the file already exists, it will be overwritten.

    Only a :class:`~pykv.store.BasicStore` can be saved. A
    :class:`~pykv.ttl.TTLStore` is rejected on purpose: its expiration
    timers use a monotonic clock that is meaningless once the program
    restarts, so quietly saving the values while losing every timer would
    be dishonest. (Teaching a TTLStore to save and restore its timers --
    by writing down the *seconds remaining* and recounting them on load --
    is a great exercise to try yourself!)

    Args:
        store: The store to save. Must be a BasicStore.
        filepath: Path to the JSON file to create or overwrite.

    Raises:
        PersistenceError: If writing to disk fails, or if a TTLStore is
            passed (its expiration timers cannot be persisted).

    """
    if isinstance(store, TTLStore):
        msg = (
            "Cannot save a TTLStore: its expiration timers cannot be persisted. "
            "Copy the values into a BasicStore first, or implement TTL "
            "persistence yourself as an exercise."
        )
        raise PersistenceError(msg)

    path = Path(filepath)
    data = store.to_dict()

    serialized: dict[str, dict[str, object]] = {}
    for key, value in data.items():
        serialized[key] = serialize_value(value)

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_text(path, json.dumps(serialized, indent=2))
    except OSError as exc:
        msg = f"Failed to save store to {path}: {exc}"
        raise PersistenceError(msg) from exc


def load_store(filepath: str | Path) -> BasicStore:
    """Load a BasicStore from a JSON file on disk.

    Like reading your saved notebook to restore all your notes.

    Args:
        filepath: Path to the JSON file to read.

    Returns:
        A new BasicStore populated with the loaded data.

    Raises:
        PersistenceError: If reading from disk or parsing the data fails.

    """
    path = Path(filepath)

    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        msg = f"Failed to load store from {path}: {exc}"
        raise PersistenceError(msg) from exc

    try:
        serialized: dict[str, dict[str, object]] = json.loads(raw)
    except json.JSONDecodeError as exc:
        msg = f"Invalid JSON in {path}: {exc}"
        raise PersistenceError(msg) from exc

    store = BasicStore()
    for key, record in serialized.items():
        value: StorableValue = deserialize_value(record)
        store.set(key, value)

    return store
