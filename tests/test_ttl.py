"""Tests for TTLStore -- key-value store with expiration support."""

import time

import pytest

from pykv.errors import KeyExpiredError, KeyNotFoundError, PyKVError
from pykv.ttl import TTLStore

# Time constants to avoid magic numbers.
SHORT_TTL = 0.05
LONG_TTL = 10.0
WAIT_FOR_EXPIRY = 0.08


class TestTTLStoreBasics:
    """Test basic set/get operations with TTL."""

    def test_set_and_get_without_ttl(self) -> None:
        """Store and retrieve a value without TTL (lives forever)."""
        store = TTLStore()
        store.set("name", "Alice")
        assert store.get("name") == "Alice"

    def test_set_and_get_with_ttl(self) -> None:
        """Store and retrieve a value before its TTL expires."""
        store = TTLStore()
        store.set("session", "abc123", ttl=LONG_TTL)
        assert store.get("session") == "abc123"

    def test_expired_key_raises(self) -> None:
        """Raise KeyExpiredError when a key has expired."""
        store = TTLStore()
        store.set("temp", "data", ttl=SHORT_TTL)
        time.sleep(WAIT_FOR_EXPIRY)
        with pytest.raises(KeyExpiredError):
            store.get("temp")

    def test_expired_key_error_is_not_key_not_found(self) -> None:
        """Distinguish an expired key from one that never existed."""
        store = TTLStore()
        store.set("temp", "data", ttl=SHORT_TTL)
        time.sleep(WAIT_FOR_EXPIRY)
        # An expired key raises KeyExpiredError, NOT KeyNotFoundError, so
        # `except KeyNotFoundError` must not catch it.
        with pytest.raises(KeyExpiredError) as exc_info:
            store.get("temp")
        assert not isinstance(exc_info.value, KeyNotFoundError)
        assert isinstance(exc_info.value, PyKVError)
        assert exc_info.value.key == "temp"

    def test_get_missing_key_raises(self) -> None:
        """Raise KeyNotFoundError for a key that was never set."""
        store = TTLStore()
        with pytest.raises(KeyNotFoundError):
            store.get("ghost")

    def test_overwrite_refreshes_ttl(self) -> None:
        """Overwrite a key to refresh its TTL."""
        store = TTLStore()
        store.set("key", "old", ttl=SHORT_TTL)
        store.set("key", "new", ttl=LONG_TTL)
        time.sleep(WAIT_FOR_EXPIRY)
        assert store.get("key") == "new"

    def test_overwrite_removes_ttl(self) -> None:
        """Overwrite a key without TTL to make it live forever."""
        store = TTLStore()
        store.set("key", "old", ttl=SHORT_TTL)
        store.set("key", "new")
        time.sleep(WAIT_FOR_EXPIRY)
        assert store.get("key") == "new"


class TestTTLStoreGetOrDefault:
    """Test get_or_default with TTL."""

    def test_returns_default_when_expired(self) -> None:
        """Return the default when the key has expired."""
        store = TTLStore()
        store.set("temp", "data", ttl=SHORT_TTL)
        time.sleep(WAIT_FOR_EXPIRY)
        assert store.get_or_default("temp", "fallback") == "fallback"

    def test_returns_value_when_alive(self) -> None:
        """Return the stored value when it has not expired."""
        store = TTLStore()
        store.set("name", "Alice", ttl=LONG_TTL)
        assert store.get_or_default("name", "fallback") == "Alice"

    def test_returns_default_for_missing(self) -> None:
        """Return default for a key that was never set."""
        store = TTLStore()
        assert store.get_or_default("ghost") is None


class TestTTLStoreDelete:
    """Test deleting keys from the TTL store."""

    def test_delete_existing(self) -> None:
        """Delete an existing key."""
        store = TTLStore()
        store.set("name", "Alice")
        assert store.delete("name") is True
        assert store.exists("name") is False

    def test_delete_missing(self) -> None:
        """Return False for a missing key."""
        store = TTLStore()
        assert store.delete("ghost") is False


class TestTTLStoreExists:
    """Test checking if keys exist with TTL."""

    def test_exists_alive(self) -> None:
        """Return True for a live key."""
        store = TTLStore()
        store.set("name", "Alice", ttl=LONG_TTL)
        assert store.exists("name") is True

    def test_exists_expired(self) -> None:
        """Return False for an expired key."""
        store = TTLStore()
        store.set("temp", "data", ttl=SHORT_TTL)
        time.sleep(WAIT_FOR_EXPIRY)
        assert store.exists("temp") is False

    def test_exists_missing(self) -> None:
        """Return False for a key that was never set."""
        store = TTLStore()
        assert store.exists("ghost") is False


class TestTTLStoreKeys:
    """Test listing keys with expiration filtering."""

    def test_keys_excludes_expired(self) -> None:
        """Exclude expired keys from the listing."""
        store = TTLStore()
        store.set("alive", "yes", ttl=LONG_TTL)
        store.set("dead", "soon", ttl=SHORT_TTL)
        time.sleep(WAIT_FOR_EXPIRY)
        assert store.keys() == ["alive"]


class TestTTLStoreRemaining:
    """Test ttl_remaining method."""

    def test_remaining_returns_seconds(self) -> None:
        """Return remaining seconds for a live key."""
        store = TTLStore()
        store.set("key", "val", ttl=LONG_TTL)
        remaining = store.ttl_remaining("key")
        assert remaining is not None
        assert remaining > 0

    def test_remaining_none_without_ttl(self) -> None:
        """Return None for a key with no TTL."""
        store = TTLStore()
        store.set("forever", "yes")
        assert store.ttl_remaining("forever") is None

    def test_remaining_raises_for_missing(self) -> None:
        """Raise KeyNotFoundError for a missing key."""
        store = TTLStore()
        with pytest.raises(KeyNotFoundError):
            store.ttl_remaining("ghost")

    def test_remaining_raises_for_expired(self) -> None:
        """Raise KeyExpiredError for an expired key."""
        store = TTLStore()
        store.set("temp", "data", ttl=SHORT_TTL)
        time.sleep(WAIT_FOR_EXPIRY)
        with pytest.raises(KeyExpiredError):
            store.ttl_remaining("temp")


class TestTTLStoreClearAndSize:
    """Test clear and size with TTL."""

    def test_clear_removes_all(self) -> None:
        """Clear all entries including TTL data."""
        store = TTLStore()
        store.set("a", 1, ttl=LONG_TTL)
        store.set("b", 2)
        store.clear()
        assert store.size() == 0

    def test_size_excludes_expired(self) -> None:
        """Exclude expired entries from the size count."""
        store = TTLStore()
        store.set("alive", "yes", ttl=LONG_TTL)
        store.set("dead", "soon", ttl=SHORT_TTL)
        time.sleep(WAIT_FOR_EXPIRY)
        assert store.size() == 1

    def test_to_dict_excludes_expired(self) -> None:
        """Exclude expired entries from the to_dict output."""
        store = TTLStore()
        store.set("alive", "yes", ttl=LONG_TTL)
        store.set("dead", "soon", ttl=SHORT_TTL)
        time.sleep(WAIT_FOR_EXPIRY)
        assert store.to_dict() == {"alive": "yes"}
