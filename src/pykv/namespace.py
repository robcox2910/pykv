"""Namespace -- group keys with prefixes like folders in a filing cabinet.

Imagine a giant filing cabinet at school. Instead of throwing all papers
into one big pile, you have folders: "math:", "science:", "english:".
When you put a paper in the "math:" folder, its full label becomes
"math:homework1". Namespaces work the same way -- they add a prefix to
every key so you can organize your data into groups.

This is super useful when multiple parts of your program share the same
store. Each part gets its own namespace so keys never collide.

Example:
    >>> store = BasicStore()
    >>> users = Namespace(store, "users:")
    >>> users.set("alice", {"age": 13})
    >>> users.get("alice")
    {'age': 13}
    >>> store.get("users:alice")  # The real key in the store
    {'age': 13}

"""

from pykv.store import BasicStore
from pykv.types import StorableValue


class Namespace:
    """A wrapper that adds a prefix to every key automatically.

    Like having your own labeled folder in a shared filing cabinet.
    Everything you store goes into your folder, and when you search
    for something, you only look in your folder.
    """

    def __init__(self, store: BasicStore, prefix: str) -> None:
        """Create a namespace that wraps an existing store.

        Args:
            store: The underlying BasicStore to use.
            prefix: The prefix to add to every key (e.g. "users:").

        """
        self._store = store
        self._prefix = prefix

    @property
    def prefix(self) -> str:
        """Return the namespace prefix."""
        return self._prefix

    def _prefixed(self, key: str) -> str:
        """Add the namespace prefix to a key.

        Args:
            key: The short key name.

        Returns:
            The full key with prefix.

        """
        return f"{self._prefix}{key}"

    def set(self, key: str, value: StorableValue) -> None:
        """Store a value under the prefixed key.

        Args:
            key: The short key name (prefix is added automatically).
            value: The data to store.

        """
        self._store.set(self._prefixed(key), value)

    def get(self, key: str) -> StorableValue:
        """Retrieve a value by its short key name.

        Args:
            key: The short key name.

        Returns:
            The stored value.

        Raises:
            KeyNotFoundError: If the prefixed key does not exist.

        """
        return self._store.get(self._prefixed(key))

    def get_or_default(self, key: str, default: StorableValue = None) -> StorableValue:
        """Retrieve a value, returning a default if missing.

        Args:
            key: The short key name.
            default: Value to return if the key is missing.

        Returns:
            The stored value, or the default.

        """
        return self._store.get_or_default(self._prefixed(key), default)

    def delete(self, key: str) -> bool:
        """Remove a key from the namespace.

        Args:
            key: The short key name.

        Returns:
            True if the key existed and was removed.

        """
        return self._store.delete(self._prefixed(key))

    def exists(self, key: str) -> bool:
        """Check whether a key exists in this namespace.

        Args:
            key: The short key name.

        Returns:
            True if the prefixed key exists.

        """
        return self._store.exists(self._prefixed(key))

    def keys(self) -> list[str]:
        """Return all keys in this namespace, without the prefix.

        Like looking at all the papers in your folder. The folder name
        is stripped off so you just see the paper names.

        Returns:
            A list of key names belonging to this namespace (prefix removed).

        """
        all_keys = self._store.keys()
        return [k[len(self._prefix) :] for k in all_keys if k.startswith(self._prefix)]

    def clear(self) -> None:
        """Remove all keys belonging to this namespace.

        Like emptying your folder but leaving everyone else's folders alone.
        """
        for key in self.keys():
            self._store.delete(self._prefixed(key))

    def size(self) -> int:
        """Return the number of keys in this namespace.

        Returns:
            The count of keys with this namespace's prefix.

        """
        return len(self.keys())
