"""Custom exceptions for PyKV.

Think of exceptions like warning signs on a road. They tell you when something
goes wrong so you can handle it properly instead of crashing. Each exception
type is like a different road sign -- "Key Not Found" is like "Road Closed",
while "Type Error" is like "Wrong Way".
"""


class PyKVError(Exception):
    """Base exception for all PyKV errors.

    Every PyKV error inherits from this class, like how every animal
    inherits from the "Animal" category. This lets you catch ALL PyKV
    errors with a single ``except PyKVError`` block.
    """


class KeyNotFoundError(PyKVError):
    """Raise when a requested key does not exist in the store.

    Imagine looking up a word in a dictionary and it is not there.
    That is what this error represents.
    """

    def __init__(self, key: str) -> None:
        """Initialize with the missing key name."""
        self.key = key
        super().__init__(f"Key not found: {key!r}")


class KeyExpiredError(PyKVError):
    """Raise when a key has expired due to its TTL.

    Like trying to drink milk after the expiration date -- the key
    existed once, but its time-to-live has passed.
    """

    def __init__(self, key: str) -> None:
        """Initialize with the expired key name."""
        self.key = key
        super().__init__(f"Key has expired: {key!r}")


class SerializationError(PyKVError):
    """Raise when a value cannot be serialized or deserialized.

    Some things cannot be written down in a notebook. If you try to
    store something that PyKV cannot convert to a saveable format,
    you get this error.
    """


class PersistenceError(PyKVError):
    """Raise when saving to or loading from disk fails.

    Like trying to save your game but the memory card is full or
    broken. Something went wrong with the file on disk.
    """


class NamespaceError(PyKVError):
    """Raise when a namespace name or a key inside a namespace breaks the rules.

    Folders in a filing cabinet must never share a paper. A namespace
    name can't be empty, and a key inside a namespace can't contain
    the ``:`` separator -- otherwise one folder could reach into another.
    """
