"""Atomic counters -- thread-safe increment and decrement.

Imagine a tally counter (the clicky thing a bouncer uses to count people
entering a club). Every time someone walks in, you click +1. Every time
someone leaves, you click -1. The key word is "atomic" -- each click is
one single, unbreakable action. Even if two people try to click at the
exact same time, the counter never gets confused.

In programming, this matters when multiple threads (like multiple workers)
try to update the same number at the same time. Without atomic operations,
two threads reading "5" at the same time might both write "6" instead of
one writing "6" and the other writing "7".

Example:
    >>> store = BasicStore()
    >>> counter = AtomicCounter(store)
    >>> counter.increment("visitors")
    1
    >>> counter.increment("visitors")
    2
    >>> counter.decrement("visitors")
    1

"""

import threading

from pykv.errors import KeyNotFoundError
from pykv.store import BasicStore
from pykv.types import StorableValue


class AtomicCounter:
    """Thread-safe counter operations on integer keys in a BasicStore.

    Like a digital tally counter that multiple people can click at the
    same time without it ever getting confused. Each click (increment
    or decrement) is guaranteed to be accurate.
    """

    def __init__(self, store: BasicStore) -> None:
        """Create an atomic counter backed by the given store.

        Args:
            store: The BasicStore to use for storing counter values.

        """
        self._store = store
        self._lock = threading.Lock()

    def increment(self, key: str, amount: int = 1) -> int:
        """Increase a counter by the given amount, creating it if needed.

        Like clicking the tally counter one or more times. If the counter
        does not exist yet, it starts at 0 before incrementing.

        Args:
            key: The counter name.
            amount: How much to add (default 1).

        Returns:
            The new counter value after incrementing.

        """
        with self._lock:
            current = self._get_int(key)
            new_value = current + amount
            self._store.set(key, new_value)
            return new_value

    def decrement(self, key: str, amount: int = 1) -> int:
        """Decrease a counter by the given amount, creating it if needed.

        Like un-clicking the tally counter. The counter can go negative
        (below zero) -- there is no floor.

        Args:
            key: The counter name.
            amount: How much to subtract (default 1).

        Returns:
            The new counter value after decrementing.

        """
        with self._lock:
            current = self._get_int(key)
            new_value = current - amount
            self._store.set(key, new_value)
            return new_value

    def get_value(self, key: str) -> int:
        """Read the current counter value.

        Like glancing at the number on the tally counter without clicking
        it. If nobody has clicked it yet, it reads 0.

        Args:
            key: The counter name.

        Returns:
            The current integer value, or 0 if the counter does not exist.

        """
        with self._lock:
            return self._get_int(key)

    def reset(self, key: str) -> None:
        """Reset a counter to zero.

        Like clearing the tally counter back to 0.

        Args:
            key: The counter name to reset.

        """
        with self._lock:
            self._store.set(key, 0)

    def _get_int(self, key: str) -> int:
        """Read the current integer value of a key, defaulting to 0.

        Args:
            key: The key to read.

        Returns:
            The integer value, or 0 if the key does not exist.

        """
        try:
            value: StorableValue = self._store.get(key)
        except KeyNotFoundError:
            return 0

        if not isinstance(value, int):
            msg = f"Counter key {key!r} holds a {type(value).__name__}, not an int"
            raise TypeError(msg)
        return value
