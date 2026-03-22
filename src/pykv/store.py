"""BasicStore -- the core key-value store for PyKV.

Imagine a giant phonebook where you can look up any name (key) and find
the phone number (value) attached to it. But unlike a real phonebook,
you can store ANY kind of information -- not just phone numbers. You can
store text, numbers, lists, and even other phonebooks (dictionaries)!

This is the simplest building block. Other modules add superpowers like
expiration, saving to disk, and batch operations on top of this.

Example:
    >>> store = BasicStore()
    >>> store.set("greeting", "Hello, world!")
    >>> store.get("greeting")
    'Hello, world!'

"""

import threading

from pykv.errors import KeyNotFoundError
from pykv.types import StorableValue


class BasicStore:
    """A simple in-memory key-value store.

    Think of this as a magical notebook where you write a label (the key)
    and the information (the value) next to it. You can add entries, look
    them up, erase them, or check if they exist.

    The store is thread-safe, meaning multiple parts of your program can
    use it at the same time without breaking things -- like a notebook
    that magically prevents two people from writing on the same line.
    """

    def __init__(self) -> None:
        """Create a new empty store."""
        self._data: dict[str, StorableValue] = {}
        self._lock = threading.Lock()

    def set(self, key: str, value: StorableValue) -> None:
        """Store a value under the given key.

        Like writing a new entry in your phonebook. If the key already
        exists, the old value is replaced -- just like erasing and
        rewriting a phone number.

        Args:
            key: The name to store the value under.
            value: The data to store (string, number, list, dict, bool, or None).

        """
        with self._lock:
            self._data[key] = value

    def get(self, key: str) -> StorableValue:
        """Retrieve the value stored under the given key.

        Like looking up a name in your phonebook to find the number.

        Args:
            key: The name to look up.

        Returns:
            The value stored under the key.

        Raises:
            KeyNotFoundError: If the key does not exist.

        """
        with self._lock:
            if key not in self._data:
                raise KeyNotFoundError(key)
            return self._data[key]

    def get_or_default(self, key: str, default: StorableValue = None) -> StorableValue:
        """Retrieve a value, returning a default if the key is missing.

        Like looking up a name in your phonebook but having a backup
        number ready in case you cannot find it.

        Args:
            key: The name to look up.
            default: The value to return if the key does not exist.

        Returns:
            The stored value, or the default if the key is missing.

        """
        with self._lock:
            return self._data.get(key, default)

    def delete(self, key: str) -> bool:
        """Remove a key and its value from the store.

        Like erasing an entry from your phonebook. If the entry was
        never there, this returns False.

        Args:
            key: The name to remove.

        Returns:
            True if the key existed and was removed, False otherwise.

        """
        with self._lock:
            if key in self._data:
                del self._data[key]
                return True
            return False

    def exists(self, key: str) -> bool:
        """Check whether a key exists in the store.

        Like flipping through your phonebook to see if a name is listed,
        without actually reading the phone number.

        Args:
            key: The name to check for.

        Returns:
            True if the key exists, False otherwise.

        """
        with self._lock:
            return key in self._data

    def keys(self) -> list[str]:
        """Return all keys currently in the store.

        Like reading every name listed in your phonebook. The values
        are not included -- just the names.

        Returns:
            A list of all key names.

        """
        with self._lock:
            return list(self._data.keys())

    def clear(self) -> None:
        """Remove all entries from the store.

        Like ripping out every page of your phonebook and starting fresh.
        """
        with self._lock:
            self._data.clear()

    def size(self) -> int:
        """Return the number of entries in the store.

        Like counting how many names are in your phonebook.

        Returns:
            The number of key-value pairs stored.

        """
        with self._lock:
            return len(self._data)

    def to_dict(self) -> dict[str, StorableValue]:
        """Return a copy of all data as a plain dictionary.

        Like photocopying your entire phonebook so someone else can
        read it without touching your original.

        Returns:
            A dictionary containing all key-value pairs.

        """
        with self._lock:
            return dict(self._data)
