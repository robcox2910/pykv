"""Namespace -- group keys into folders, like a filing cabinet.

Imagine a giant filing cabinet at school. Instead of throwing all papers
into one big pile, you have folders: "math", "science", "english".
When you put a paper in the "math" folder, its full label becomes
"math:homework1". Namespaces work the same way -- they stamp the folder
name and a ``:`` onto every key so you can organize your data into groups.

Folders can sit inside folders: "users:admin" is a folder inside "users".
So ``:`` is the *separator* that splits folder names from paper names, and
there is one rule that keeps everything tidy:

    A key inside a namespace can never contain ``:``.

Why? Without the rule, the "users" folder could file a paper called
"admin:alice", which is exactly the label of "alice" in the "users:admin"
folder -- two folders sharing one paper. With the rule, the folder is
always everything before the *last* ``:``, so every label in the store
belongs to exactly one folder. A key with ``:`` in it raises
``NamespaceError``.

Example:
    >>> store = BasicStore()
    >>> users = Namespace(store, "users")
    >>> users.set("alice", {"age": 13})
    >>> users.get("alice")
    {'age': 13}
    >>> store.get("users:alice")  # The real key in the store
    {'age': 13}

"""

from pykv.errors import NamespaceError
from pykv.store import BasicStore
from pykv.types import StorableValue

SEPARATOR = ":"
"""The character between a folder name and a key: ``users:alice``."""


class Namespace:
    """A wrapper that files every key inside one named folder.

    Like having your own labeled folder in a shared filing cabinet.
    Everything you store goes into your folder, and when you search
    for something, you only look in your folder -- never inside the
    folders nested in it, and never in anyone else's.
    """

    def __init__(self, store: BasicStore, prefix: str) -> None:
        """Create a namespace that wraps an existing store.

        Args:
            store: The underlying BasicStore to use.
            prefix: The folder name, such as ``"users"`` or, for a folder
                inside another, ``"users:admin"``. A trailing ``:`` is
                optional, so ``"users:"`` means the same as ``"users"``.

        Raises:
            NamespaceError: If the name is empty or has an empty part,
                like ``""``, ``":"`` or ``"users::admin"``.

        """
        name = prefix.removesuffix(SEPARATOR)
        if "" in name.split(SEPARATOR):
            msg = (
                f"Bad namespace name {prefix!r}: it must not be empty, and every part "
                f"between {SEPARATOR!r} separators needs at least one character"
            )
            raise NamespaceError(msg)
        self._store = store
        self._name = name
        self._prefix = name + SEPARATOR

    @property
    def name(self) -> str:
        """Return the folder name, without the trailing separator (e.g. ``"users"``)."""
        return self._name

    @property
    def prefix(self) -> str:
        """Return the label stamped in front of every key (e.g. ``"users:"``)."""
        return self._prefix

    def _prefixed(self, key: str) -> str:
        """Add the namespace prefix to a key, after checking the key is allowed.

        Args:
            key: The short key name.

        Returns:
            The full key with prefix.

        Raises:
            NamespaceError: If the key contains the ``:`` separator.

        """
        if SEPARATOR in key:
            msg = (
                f"Key {key!r} contains {SEPARATOR!r}, which separates folder names: "
                f"in namespace {self._name!r} it could clash with a nested folder. "
                f"Use a nested Namespace (e.g. {self._name + SEPARATOR + 'admin'!r}) instead"
            )
            raise NamespaceError(msg)
        return self._prefix + key

    def set(self, key: str, value: StorableValue) -> None:
        """Store a value, filing it inside this namespace's folder.

        Like dropping a paper into your own labeled folder -- the folder
        name is stamped onto the key automatically.

        Args:
            key: The short key name (prefix is added automatically).
            value: The data to store.

        Raises:
            NamespaceError: If the key contains the ``:`` separator.

        """
        self._store.set(self._prefixed(key), value)

    def get(self, key: str) -> StorableValue:
        """Retrieve a value by its short key name.

        Like pulling a paper out of your own folder by its short name --
        you never have to write out the folder prefix yourself.

        Args:
            key: The short key name.

        Returns:
            The stored value.

        Raises:
            KeyNotFoundError: If the prefixed key does not exist.
            NamespaceError: If the key contains the ``:`` separator.

        """
        return self._store.get(self._prefixed(key))

    def get_or_default(self, key: str, default: StorableValue = None) -> StorableValue:
        """Retrieve a value, returning a default if missing.

        Like looking in your folder for a paper but having a spare copy
        ready in case it is not filed there.

        Args:
            key: The short key name.
            default: Value to return if the key is missing.

        Returns:
            The stored value, or the default.

        Raises:
            NamespaceError: If the key contains the ``:`` separator.

        """
        return self._store.get_or_default(self._prefixed(key), default)

    def delete(self, key: str) -> bool:
        """Remove a key from the namespace.

        Like taking a single paper out of your folder and shredding it.

        Args:
            key: The short key name.

        Returns:
            True if the key existed and was removed.

        Raises:
            NamespaceError: If the key contains the ``:`` separator.

        """
        return self._store.delete(self._prefixed(key))

    def exists(self, key: str) -> bool:
        """Check whether a key exists in this namespace.

        Like flipping through your folder to see if a paper is filed
        there, without pulling it out.

        Args:
            key: The short key name.

        Returns:
            True if the prefixed key exists.

        Raises:
            NamespaceError: If the key contains the ``:`` separator.

        """
        return self._store.exists(self._prefixed(key))

    def keys(self) -> list[str]:
        """Return all keys in this namespace, without the prefix.

        Like looking at all the papers in your folder. The folder name
        is stripped off so you just see the paper names. Papers in a
        folder *inside* yours (their names still contain ``:``) belong
        to that folder, so they are left out.

        Returns:
            A list of key names belonging to this namespace (prefix removed).

        """
        all_keys = self._store.keys()
        start = len(self._prefix)
        return [
            k[start:] for k in all_keys if k.startswith(self._prefix) and SEPARATOR not in k[start:]
        ]

    def clear(self) -> None:
        """Remove all keys belonging to this namespace.

        Like emptying your folder but leaving everyone else's folders
        alone, including the folders nested inside yours.
        """
        for key in self.keys():
            self._store.delete(self._prefix + key)

    def size(self) -> int:
        """Return the number of keys in this namespace.

        Like counting only the papers in your own folder, ignoring
        everyone else's folders in the cabinet and the folders nested
        inside yours.

        Returns:
            The number of keys that ``keys()`` lists.

        """
        return len(self.keys())
