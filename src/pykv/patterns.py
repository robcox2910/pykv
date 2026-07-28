"""Pattern matching -- find keys using glob patterns.

Imagine you have a messy desk covered in sticky notes. Some say "todo:*",
some say "meeting:*", and some say "idea:*". Pattern matching lets you
quickly find all the sticky notes that match a certain pattern -- like
"give me all notes that start with todo:".

PyKV uses glob-style patterns, the same kind you use when searching for
files on your computer:
- ``*`` matches anything (zero or more characters)
- ``?`` matches exactly one character
- ``[abc]`` matches any one of a, b, or c

Example:
    >>> store = BasicStore()
    >>> store.set("user:alice", "admin")
    >>> store.set("user:bob", "member")
    >>> store.set("post:1", "Hello!")
    >>> match_keys(store, "user:*")
    ['user:alice', 'user:bob']

"""

import fnmatch

from pykv.store import BasicStore
from pykv.types import StorableValue


def match_keys(store: BasicStore, pattern: str) -> list[str]:
    """Find all keys that match a glob pattern.

    Like searching your desk for sticky notes that match a description.
    Uses the same wildcards as file searches: ``*``, ``?``, ``[abc]``.
    Matching is always case-sensitive, so ``"User:*"`` will not match
    ``"user:alice"`` -- the behavior is the same on every operating system.

    Args:
        store: The store to search.
        pattern: A glob pattern (e.g. "user:*", "item_?", "log[12]").

    Returns:
        A sorted list of matching key names.

    """
    all_keys = store.keys()
    matched = [key for key in all_keys if fnmatch.fnmatchcase(key, pattern)]
    return sorted(matched)


def match_items(
    store: BasicStore,
    pattern: str,
) -> dict[str, StorableValue]:
    """Find all key-value pairs where the key matches a glob pattern.

    Like finding all matching sticky notes AND reading what they say.

    Args:
        store: The store to search.
        pattern: A glob pattern (e.g. "user:*").

    Returns:
        A dictionary of matching key-value pairs.

    """
    matched_keys = match_keys(store, pattern)
    return {key: store.get(key) for key in matched_keys}


def count_matches(store: BasicStore, pattern: str) -> int:
    """Count how many keys match a glob pattern.

    Like counting how many sticky notes match a description without
    reading them.

    Args:
        store: The store to search.
        pattern: A glob pattern.

    Returns:
        The number of matching keys.

    """
    return len(match_keys(store, pattern))
