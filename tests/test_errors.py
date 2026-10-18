"""Tests for custom exceptions."""

from pykv.errors import (
    KeyExpiredError,
    KeyNotFoundError,
    NamespaceError,
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

    def test_namespace_is_pykv_error(self) -> None:
        """Verify NamespaceError is a PyKVError."""
        assert issubclass(NamespaceError, PyKVError)


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


class TestPackageExports:
    """Every PyKV error can be imported straight from ``pykv``."""

    def test_namespace_error_is_exported(self) -> None:
        """Import NamespaceError from the package, like the other errors."""
        # Imported inside the test, so a missing name fails only this test.
        import pykv  # noqa: PLC0415
        from pykv import NamespaceError as Exported  # noqa: PLC0415

        assert Exported is NamespaceError
        assert "NamespaceError" in pykv.__all__
