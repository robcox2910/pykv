"""Batch operations -- get and set multiple keys at once.

Imagine going to the grocery store. You could make one trip for each item
on your list -- milk, bread, eggs -- but that would be exhausting! Instead,
you take your whole shopping list and grab everything in one trip. Batch
operations work the same way: instead of calling get() or set() over and
over, you do it all at once.

This is faster and more convenient, especially when you have lots of keys
to work with.

Example:
    >>> store = BasicStore()
    >>> batch_set(store, {"name": "Alice", "age": 13, "grade": 8})
    >>> batch_get(store, ["name", "age"])
    {'name': 'Alice', 'age': 13}

"""

from pykv.store import BasicStore
from pykv.types import StorableValue


def batch_set(store: BasicStore, items: dict[str, StorableValue]) -> None:
    """Set multiple key-value pairs in one call.

    Like dropping off your whole grocery bag at once instead of
    putting items away one by one.

    Args:
        store: The store to write to.
        items: A dictionary of key-value pairs to set.

    """
    for key, value in items.items():
        store.set(key, value)


def batch_get(
    store: BasicStore,
    keys: list[str],
    *,
    skip_missing: bool = False,
) -> dict[str, StorableValue]:
    """Retrieve multiple values in one call.

    Like reading multiple entries from your phonebook at once.
    If ``skip_missing`` is True, keys that do not exist are silently
    skipped. Otherwise, a ``KeyNotFoundError`` is raised for any
    missing key.

    Args:
        store: The store to read from.
        keys: A list of keys to retrieve.
        skip_missing: If True, skip keys that do not exist instead of raising.

    Returns:
        A dictionary of the found key-value pairs.

    Raises:
        KeyNotFoundError: If a key is missing and skip_missing is False.

    """
    result: dict[str, StorableValue] = {}
    for key in keys:
        if skip_missing:
            if store.exists(key):
                result[key] = store.get(key)
        else:
            result[key] = store.get(key)
    return result


def batch_delete(store: BasicStore, keys: list[str]) -> int:
    """Delete multiple keys in one call.

    Like erasing several entries from your phonebook at once.

    Args:
        store: The store to delete from.
        keys: A list of keys to remove.

    Returns:
        The number of keys that were actually deleted.

    """
    count = 0
    for key in keys:
        if store.delete(key):
            count += 1
    return count


def batch_exists(store: BasicStore, keys: list[str]) -> dict[str, bool]:
    """Check whether multiple keys exist in one call.

    Like scanning your phonebook for a list of names and marking
    which ones you found.

    Args:
        store: The store to check.
        keys: A list of keys to look for.

    Returns:
        A dictionary mapping each key to True/False.

    """
    return {key: store.exists(key) for key in keys}
