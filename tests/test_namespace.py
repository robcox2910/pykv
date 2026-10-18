"""Tests for Namespace -- key prefixing like folders in a filing cabinet."""

import pytest

from pykv.errors import KeyNotFoundError, NamespaceError
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


class TestNestedNamespacesDoNotOverlap:
    """Two folders must never share a paper, even when one sits inside the other."""

    def test_parent_keys_skip_the_nested_folder(self) -> None:
        """List only the parent's own keys, not the nested namespace's keys."""
        store = BasicStore()
        users = Namespace(store, "users:")
        admins = Namespace(store, "users:admin:")
        users.set("bob", 1)
        admins.set("alice", 2)
        assert users.keys() == ["bob"]
        assert admins.keys() == ["alice"]

    def test_parent_size_skips_the_nested_folder(self) -> None:
        """Count only the parent's own keys, not the nested namespace's keys."""
        store = BasicStore()
        users = Namespace(store, "users:")
        admins = Namespace(store, "users:admin:")
        admins.set("alice", 2)
        assert users.size() == 0
        assert admins.size() == 1

    def test_parent_clear_leaves_the_nested_folder_alone(self) -> None:
        """Clearing the parent must not wipe the nested namespace."""
        store = BasicStore()
        users = Namespace(store, "users:")
        admins = Namespace(store, "users:admin:")
        users.set("bob", 1)
        admins.set("alice", 2)
        users.clear()
        assert users.size() == 0
        assert admins.get("alice") == 2  # noqa: PLR2004

    def test_nested_clear_leaves_the_parent_alone(self) -> None:
        """Clearing the nested namespace must not touch the parent's keys."""
        store = BasicStore()
        users = Namespace(store, "users")
        admins = Namespace(store, "users:admin")
        users.set("bob", 1)
        admins.set("alice", 2)
        admins.clear()
        assert users.get("bob") == 1
        assert admins.size() == 0

    def test_key_with_separator_cannot_reach_another_folder(self) -> None:
        """Refuse a key containing ':' so it can't land on another namespace's key."""
        store = BasicStore()
        users = Namespace(store, "users:")
        admins = Namespace(store, "users:admin:")
        admins.set("alice", 2)
        with pytest.raises(NamespaceError, match="':'"):
            users.set("admin:alice", 1)
        assert admins.get("alice") == 2  # noqa: PLR2004

    @pytest.mark.parametrize("method", ["get", "get_or_default", "delete", "exists"])
    def test_every_key_method_refuses_the_separator(self, method: str) -> None:
        """Refuse a key containing ':' on reads and deletes too, not just on set."""
        store = BasicStore()
        users = Namespace(store, "users")
        store.set("users:admin:alice", 2)
        with pytest.raises(NamespaceError):
            getattr(users, method)("admin:alice")
        assert store.get("users:admin:alice") == 2  # noqa: PLR2004


class TestNamespaceName:
    """The name is the folder label; a trailing ':' is optional."""

    def test_trailing_separator_is_optional(self) -> None:
        """Treat "users" and "users:" as the same folder."""
        store = BasicStore()
        Namespace(store, "users").set("alice", 1)
        assert Namespace(store, "users:").get("alice") == 1
        assert store.get("users:alice") == 1

    def test_name_and_prefix(self) -> None:
        """Expose the name without the separator and the prefix with it."""
        store = BasicStore()
        for given in ("users:admin", "users:admin:"):
            ns = Namespace(store, given)
            assert ns.name == "users:admin"
            assert ns.prefix == "users:admin:"

    def test_nested_name_files_keys_under_both_labels(self) -> None:
        """Store a nested namespace's key as name + ':' + key."""
        store = BasicStore()
        Namespace(store, "users:admin").set("alice", 1)
        assert store.keys() == ["users:admin:alice"]

    @pytest.mark.parametrize("bad_name", ["", ":", "::", ":users", "users::admin", "users::"])
    def test_name_with_an_empty_part_is_refused(self, bad_name: str) -> None:
        """Refuse a name that is empty or has an empty part between separators."""
        with pytest.raises(NamespaceError):
            Namespace(BasicStore(), bad_name)

    def test_empty_key_is_allowed(self) -> None:
        """Allow the empty key: it is still a paper in exactly one folder."""
        store = BasicStore()
        users = Namespace(store, "users")
        users.set("", 1)
        assert users.keys() == [""]
        assert store.get("users:") == 1
