"""Tests for Namespace -- key prefixing like folders in a filing cabinet."""

import pytest

from pykv.errors import KeyNotFoundError
from pykv.namespace import Namespace
from pykv.store import BasicStore


class TestNamespaceSetAndGet:
    """Test setting and getting values through a namespace."""

    def test_set_and_get(self) -> None:
        """Set and get a value through a namespace."""
        store = BasicStore()
        ns = Namespace(store, "users:")
        ns.set("alice", "admin")
        assert ns.get("alice") == "admin"

    def test_key_is_prefixed_in_store(self) -> None:
        """Verify that the key is stored with its prefix."""
        store = BasicStore()
        ns = Namespace(store, "users:")
        ns.set("alice", "admin")
        assert store.get("users:alice") == "admin"

    def test_get_missing_raises(self) -> None:
        """Raise KeyNotFoundError for a missing namespaced key."""
        store = BasicStore()
        ns = Namespace(store, "users:")
        with pytest.raises(KeyNotFoundError):
            ns.get("ghost")

    def test_get_or_default_missing(self) -> None:
        """Return default for a missing namespaced key."""
        store = BasicStore()
        ns = Namespace(store, "users:")
        assert ns.get_or_default("ghost", "nobody") == "nobody"


class TestNamespacePrefix:
    """Test the prefix property."""

    def test_prefix_property(self) -> None:
        """Return the namespace prefix."""
        store = BasicStore()
        ns = Namespace(store, "cache:")
        assert ns.prefix == "cache:"


class TestNamespaceDelete:
    """Test deleting through a namespace."""

    def test_delete_existing(self) -> None:
        """Delete an existing namespaced key."""
        store = BasicStore()
        ns = Namespace(store, "users:")
        ns.set("alice", "admin")
        assert ns.delete("alice") is True
        assert ns.exists("alice") is False

    def test_delete_missing(self) -> None:
        """Return False when deleting a missing namespaced key."""
        store = BasicStore()
        ns = Namespace(store, "users:")
        assert ns.delete("ghost") is False


class TestNamespaceExists:
    """Test existence checks through a namespace."""

    def test_exists_true(self) -> None:
        """Return True for an existing namespaced key."""
        store = BasicStore()
        ns = Namespace(store, "users:")
        ns.set("alice", "admin")
        assert ns.exists("alice") is True

    def test_exists_false(self) -> None:
        """Return False for a missing namespaced key."""
        store = BasicStore()
        ns = Namespace(store, "users:")
        assert ns.exists("ghost") is False


class TestNamespaceKeys:
    """Test listing keys within a namespace."""

    def test_keys_returns_only_namespaced(self) -> None:
        """Return only keys belonging to this namespace, without prefix."""
        store = BasicStore()
        users = Namespace(store, "users:")
        posts = Namespace(store, "posts:")
        users.set("alice", "admin")
        users.set("bob", "member")
        posts.set("1", "Hello")
        assert sorted(users.keys()) == ["alice", "bob"]
        assert posts.keys() == ["1"]

    def test_keys_empty(self) -> None:
        """Return empty list for an empty namespace."""
        store = BasicStore()
        ns = Namespace(store, "empty:")
        assert ns.keys() == []


class TestNamespaceClearAndSize:
    """Test clearing and sizing a namespace."""

    def test_clear_only_removes_namespaced_keys(self) -> None:
        """Clear only keys in this namespace, not others."""
        store = BasicStore()
        users = Namespace(store, "users:")
        posts = Namespace(store, "posts:")
        users.set("alice", "admin")
        posts.set("1", "Hello")
        users.clear()
        assert users.size() == 0
        assert posts.size() == 1

    def test_size_counts_namespaced(self) -> None:
        """Count only keys in this namespace."""
        store = BasicStore()
        ns = Namespace(store, "items:")
        ns.set("a", 1)
        ns.set("b", 2)
        expected_size = 2
        assert ns.size() == expected_size


class TestMultipleNamespaces:
    """Test using multiple namespaces on the same store."""

    def test_isolation_between_namespaces(self) -> None:
        """Ensure namespaces do not interfere with each other."""
        store = BasicStore()
        ns_a = Namespace(store, "a:")
        ns_b = Namespace(store, "b:")
        ns_a.set("key", "value_a")
        ns_b.set("key", "value_b")
        assert ns_a.get("key") == "value_a"
        assert ns_b.get("key") == "value_b"
