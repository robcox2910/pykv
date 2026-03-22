"""Tests for custom exceptions."""

from pykv.errors import (
    KeyExpiredError,
    KeyNotFoundError,
    PersistenceError,
    PyKVError,
    SerializationError,
)


class TestExceptionHierarchy:
    """Test that all exceptions inherit from PyKVError."""

    def test_key_not_found_is_pykv_error(self) -> None:
        """Verify KeyNotFoundError is a PyKVError."""
        assert issubclass(KeyNotFoundError, PyKVError)

    def test_key_expired_is_pykv_error(self) -> None:
        """Verify KeyExpiredError is a PyKVError."""
        assert issubclass(KeyExpiredError, PyKVError)

    def test_serialization_is_pykv_error(self) -> None:
        """Verify SerializationError is a PyKVError."""
        assert issubclass(SerializationError, PyKVError)

    def test_persistence_is_pykv_error(self) -> None:
        """Verify PersistenceError is a PyKVError."""
        assert issubclass(PersistenceError, PyKVError)


class TestKeyNotFoundError:
    """Test KeyNotFoundError attributes and message."""

    def test_stores_key(self) -> None:
        """Store the missing key name on the exception."""
        err = KeyNotFoundError("my_key")
        assert err.key == "my_key"

    def test_message(self) -> None:
        """Include the key name in the error message."""
        err = KeyNotFoundError("my_key")
        assert "my_key" in str(err)


class TestKeyExpiredError:
    """Test KeyExpiredError attributes and message."""

    def test_stores_key(self) -> None:
        """Store the expired key name on the exception."""
        err = KeyExpiredError("session")
        assert err.key == "session"

    def test_message(self) -> None:
        """Include the key name in the error message."""
        err = KeyExpiredError("session")
        assert "session" in str(err)
