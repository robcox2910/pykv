"""TTLStore -- key-value store with expiration support.

Imagine you buy a carton of milk from the store. On the side, there is a
date that says "Best before June 1". After that date, the milk expires
and you should throw it away. TTL (Time To Live) works the same way for
your stored data -- you set a timer and when it runs out, the key
automatically disappears.

This is useful for things like:
- Caching a web page for 5 minutes
- Storing a login session that expires after 1 hour
- Keeping a temporary lock that releases after 30 seconds

Example:
    >>> store = TTLStore()
    >>> store.set("session", "abc123", ttl=60.0)  # Expires in 60 seconds
    >>> store.get("session")
    'abc123'

"""

import threading
import time

from pykv.errors import KeyNotFoundError
from pykv.types import StorableValue


class TTLStore:
    """A key-value store where keys can have expiration times.

    Like a refrigerator with smart labels -- each item has an optional
    expiration date. When you try to grab something that has expired,
    the fridge automatically throws it away and tells you it is gone.

    You can also set keys without a TTL, and they will live forever
    (like canned food that never expires).
    """

    def __init__(self) -> None:
        """Create a new empty TTL store."""
        self._data: dict[str, StorableValue] = {}
        self._expiry: dict[str, float] = {}
        self._lock = threading.Lock()

    def _is_expired(self, key: str) -> bool:
        """Check if a key has passed its expiration time.

        Args:
            key: The key to check.

        Returns:
            True if the key has a TTL and it has expired.

        """
        if key in self._expiry:
            return time.monotonic() >= self._expiry[key]
        return False

    def _evict_if_expired(self, key: str) -> bool:
        """Remove a key if it has expired.

        Args:
            key: The key to check and possibly remove.

        Returns:
            True if the key was expired and removed.

        """
        if self._is_expired(key):
            del self._data[key]
            del self._expiry[key]
            return True
        return False

    def set(self, key: str, value: StorableValue, ttl: float | None = None) -> None:
        """Store a value with an optional time-to-live.

        Like putting milk in the fridge with an expiration sticker.
        If you do not provide a TTL, the item never expires.

        Args:
            key: The name to store the value under.
            value: The data to store.
            ttl: Seconds until the key expires. None means no expiration.

        """
        with self._lock:
            self._data[key] = value
            if ttl is not None:
                self._expiry[key] = time.monotonic() + ttl
            elif key in self._expiry:
                # If resetting without TTL, remove the old expiration.
                del self._expiry[key]

    def get(self, key: str) -> StorableValue:
        """Retrieve a value, raising an error if missing or expired.

        Like reaching into the fridge -- if the milk has expired,
        the fridge throws it away and tells you it is gone.

        Args:
            key: The name to look up.

        Returns:
            The stored value.

        Raises:
            KeyNotFoundError: If the key does not exist or has expired.

        """
        with self._lock:
            if key not in self._data:
                raise KeyNotFoundError(key)
            if self._evict_if_expired(key):
                raise KeyNotFoundError(key)
            return self._data[key]

    def get_or_default(self, key: str, default: StorableValue = None) -> StorableValue:
        """Retrieve a value, returning a default if missing or expired.

        Args:
            key: The name to look up.
            default: Value to return if the key is missing or expired.

        Returns:
            The stored value, or the default.

        """
        with self._lock:
            if key not in self._data:
                return default
            if self._evict_if_expired(key):
                return default
            return self._data[key]

    def delete(self, key: str) -> bool:
        """Remove a key and its value from the store.

        Args:
            key: The name to remove.

        Returns:
            True if the key existed and was removed, False otherwise.

        """
        with self._lock:
            if key in self._data:
                del self._data[key]
                self._expiry.pop(key, None)
                return True
            return False

    def exists(self, key: str) -> bool:
        """Check whether a key exists and has not expired.

        Args:
            key: The name to check for.

        Returns:
            True if the key exists and has not expired.

        """
        with self._lock:
            if key not in self._data:
                return False
            return not self._evict_if_expired(key)

    def keys(self) -> list[str]:
        """Return all non-expired keys.

        Returns:
            A list of all key names that have not expired.

        """
        with self._lock:
            # Evict expired keys first.
            expired = [k for k in self._data if self._is_expired(k)]
            for k in expired:
                del self._data[k]
                del self._expiry[k]
            return list(self._data.keys())

    def ttl_remaining(self, key: str) -> float | None:
        """Return the remaining time-to-live for a key in seconds.

        Like checking the expiration date on your milk to see how many
        days you have left before it goes bad.

        Args:
            key: The key to check.

        Returns:
            Seconds remaining, or None if the key has no TTL.

        Raises:
            KeyNotFoundError: If the key does not exist or has expired.

        """
        with self._lock:
            if key not in self._data:
                raise KeyNotFoundError(key)
            if self._evict_if_expired(key):
                raise KeyNotFoundError(key)
            if key not in self._expiry:
                return None
            return max(0.0, self._expiry[key] - time.monotonic())

    def clear(self) -> None:
        """Remove all entries from the store."""
        with self._lock:
            self._data.clear()
            self._expiry.clear()

    def size(self) -> int:
        """Return the number of non-expired entries.

        Returns:
            The count of active (non-expired) key-value pairs.

        """
        with self._lock:
            expired = [k for k in self._data if self._is_expired(k)]
            for k in expired:
                del self._data[k]
                del self._expiry[k]
            return len(self._data)

    def to_dict(self) -> dict[str, StorableValue]:
        """Return a copy of all non-expired data.

        Returns:
            A dictionary of all active key-value pairs.

        """
        with self._lock:
            expired = [k for k in self._data if self._is_expired(k)]
            for k in expired:
                del self._data[k]
                del self._expiry[k]
            return dict(self._data)
