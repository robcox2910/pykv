"""Tests for BasicStore -- the core key-value store."""

import threading

import pytest

from pykv.errors import KeyNotFoundError
from pykv.store import BasicStore

EXPECTED_AGE = 13


class TestBasicStoreSetAndGet:
    """Test setting and getting values from the store."""

    def test_set_and_get_string(self) -> None:
        """Set and retrieve a string value."""
        store = BasicStore()
        store.set("name", "Alice")
        assert store.get("name") == "Alice"

    def test_set_and_get_integer(self) -> None:
        """Set and retrieve an integer value."""
        store = BasicStore()
        store.set("age", 13)
        assert store.get("age") == EXPECTED_AGE

    def test_set_and_get_float(self) -> None:
        """Set and retrieve a float value."""
        store = BasicStore()
        store.set("pi", 3.14)
        assert store.get("pi") == pytest.approx(3.14)

    def test_set_and_get_list(self) -> None:
        """Set and retrieve a list value."""
        store = BasicStore()
        store.set("colors", ["red", "green", "blue"])
        assert store.get("colors") == ["red", "green", "blue"]

    def test_set_and_get_dict(self) -> None:
        """Set and retrieve a dict value."""
        store = BasicStore()
        store.set("user", {"name": "Alice", "age": 13})
        assert store.get("user") == {"name": "Alice", "age": 13}

    def test_set_and_get_bool(self) -> None:
        """Set and retrieve boolean values."""
        store = BasicStore()
        store.set("active", True)
        assert store.get("active") is True

    def test_set_and_get_none(self) -> None:
        """Set and retrieve None."""
        store = BasicStore()
        store.set("empty", None)
        assert store.get("empty") is None

    def test_overwrite_existing_key(self) -> None:
        """Overwrite an existing key with a new value."""
        store = BasicStore()
        store.set("color", "red")
        store.set("color", "blue")
        assert store.get("color") == "blue"

    def test_get_missing_key_raises(self) -> None:
        """Raise KeyNotFoundError when getting a missing key."""
        store = BasicStore()
        with pytest.raises(KeyNotFoundError, match="greeting"):
            store.get("greeting")


class TestBasicStoreGetOrDefault:
    """Test the get_or_default method."""

    def test_returns_value_when_exists(self) -> None:
        """Return the stored value when the key exists."""
        store = BasicStore()
        store.set("name", "Alice")
        assert store.get_or_default("name", "Unknown") == "Alice"

    def test_returns_default_when_missing(self) -> None:
        """Return the default when the key does not exist."""
        store = BasicStore()
        assert store.get_or_default("name", "Unknown") == "Unknown"

    def test_returns_none_as_default(self) -> None:
        """Return None as the default when no default is specified."""
        store = BasicStore()
        assert store.get_or_default("name") is None


class TestBasicStoreDelete:
    """Test deleting keys from the store."""

    def test_delete_existing_key(self) -> None:
        """Delete an existing key and return True."""
        store = BasicStore()
        store.set("name", "Alice")
        assert store.delete("name") is True
        assert store.exists("name") is False

    def test_delete_missing_key(self) -> None:
        """Return False when deleting a key that does not exist."""
        store = BasicStore()
        assert store.delete("ghost") is False


class TestBasicStoreExists:
    """Test checking if keys exist."""

    def test_exists_returns_true(self) -> None:
        """Return True for an existing key."""
        store = BasicStore()
        store.set("name", "Alice")
        assert store.exists("name") is True

    def test_exists_returns_false(self) -> None:
        """Return False for a missing key."""
        store = BasicStore()
        assert store.exists("ghost") is False


class TestBasicStoreKeys:
    """Test listing all keys."""

    def test_keys_empty_store(self) -> None:
        """Return an empty list for an empty store."""
        store = BasicStore()
        assert store.keys() == []

    def test_keys_with_data(self) -> None:
        """Return all keys in the store."""
        store = BasicStore()
        store.set("a", 1)
        store.set("b", 2)
        assert sorted(store.keys()) == ["a", "b"]


class TestBasicStoreClearAndSize:
    """Test clearing the store and checking its size."""

    def test_clear_removes_all(self) -> None:
        """Clear all data from the store."""
        store = BasicStore()
        store.set("a", 1)
        store.set("b", 2)
        store.clear()
        assert store.size() == 0

    def test_size_tracks_entries(self) -> None:
        """Track the correct number of entries."""
        store = BasicStore()
        assert store.size() == 0
        store.set("a", 1)
        assert store.size() == 1
        store.set("b", 2)
        expected_size = 2
        assert store.size() == expected_size


class TestBasicStoreToDict:
    """Test converting the store to a plain dictionary."""

    def test_to_dict_returns_copy(self) -> None:
        """Return a copy, not a reference to internal data."""
        store = BasicStore()
        store.set("name", "Alice")
        data = store.to_dict()
        data["name"] = "Bob"
        assert store.get("name") == "Alice"


class TestBasicStoreThreadSafety:
    """Test thread safety of the store."""

    def test_concurrent_set(self) -> None:
        """Handle concurrent writes without data corruption."""
        store = BasicStore()
        iterations = 100

        def writer(prefix: str) -> None:
            for i in range(iterations):
                store.set(f"{prefix}:{i}", i)

        threads = [threading.Thread(target=writer, args=(f"t{t}",)) for t in range(4)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        expected_size = 400
        assert store.size() == expected_size
