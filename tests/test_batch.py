"""Tests for batch operations -- get and set multiple keys at once."""

import pytest

from pykv.batch import batch_delete, batch_exists, batch_get, batch_set
from pykv.errors import KeyNotFoundError
from pykv.store import BasicStore

EXPECTED_AGE = 13


class TestBatchSet:
    """Test setting multiple keys at once."""

    def test_batch_set_multiple(self) -> None:
        """Set multiple keys in one call."""
        store = BasicStore()
        batch_set(store, {"name": "Alice", "age": 13, "active": True})
        assert store.get("name") == "Alice"
        assert store.get("age") == EXPECTED_AGE
        assert store.get("active") is True

    def test_batch_set_empty(self) -> None:
        """Handle an empty batch without errors."""
        store = BasicStore()
        batch_set(store, {})
        assert store.size() == 0


class TestBatchGet:
    """Test getting multiple keys at once."""

    def test_batch_get_all_exist(self) -> None:
        """Retrieve all requested keys."""
        store = BasicStore()
        batch_set(store, {"a": 1, "b": 2, "c": 3})
        result = batch_get(store, ["a", "c"])
        assert result == {"a": 1, "c": 3}

    def test_batch_get_missing_raises(self) -> None:
        """Raise KeyNotFoundError when a key is missing."""
        store = BasicStore()
        store.set("a", 1)
        with pytest.raises(KeyNotFoundError):
            batch_get(store, ["a", "missing"])

    def test_batch_get_skip_missing(self) -> None:
        """Skip missing keys when skip_missing is True."""
        store = BasicStore()
        store.set("a", 1)
        result = batch_get(store, ["a", "missing"], skip_missing=True)
        assert result == {"a": 1}

    def test_batch_get_empty_list(self) -> None:
        """Handle an empty key list without errors."""
        store = BasicStore()
        result = batch_get(store, [])
        assert result == {}


class TestBatchDelete:
    """Test deleting multiple keys at once."""

    def test_batch_delete_existing(self) -> None:
        """Delete multiple existing keys and return the count."""
        store = BasicStore()
        batch_set(store, {"a": 1, "b": 2, "c": 3})
        deleted_count = 3
        assert batch_delete(store, ["a", "b", "c"]) == deleted_count
        assert store.size() == 0

    def test_batch_delete_partial(self) -> None:
        """Return the count of actually deleted keys."""
        store = BasicStore()
        store.set("a", 1)
        assert batch_delete(store, ["a", "ghost"]) == 1

    def test_batch_delete_empty(self) -> None:
        """Handle an empty key list without errors."""
        store = BasicStore()
        assert batch_delete(store, []) == 0


class TestBatchExists:
    """Test checking existence of multiple keys at once."""

    def test_batch_exists_mixed(self) -> None:
        """Check multiple keys with mixed existence."""
        store = BasicStore()
        store.set("a", 1)
        result = batch_exists(store, ["a", "ghost"])
        assert result == {"a": True, "ghost": False}

    def test_batch_exists_empty(self) -> None:
        """Handle an empty key list without errors."""
        store = BasicStore()
        result = batch_exists(store, [])
        assert result == {}
