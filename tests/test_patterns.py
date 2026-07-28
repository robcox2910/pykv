"""Tests for pattern matching -- find keys using glob patterns."""

from pykv.patterns import count_matches, match_items, match_keys
from pykv.store import BasicStore


class TestMatchKeys:
    """Test finding keys by glob pattern."""

    def test_match_star_wildcard(self) -> None:
        """Match keys using the * wildcard."""
        store = BasicStore()
        store.set("user:alice", "admin")
        store.set("user:bob", "member")
        store.set("post:1", "Hello")
        assert match_keys(store, "user:*") == ["user:alice", "user:bob"]

    def test_match_question_mark(self) -> None:
        """Match keys using the ? wildcard (single character)."""
        store = BasicStore()
        store.set("log1", "a")
        store.set("log2", "b")
        store.set("log10", "c")
        assert match_keys(store, "log?") == ["log1", "log2"]

    def test_match_bracket(self) -> None:
        """Match keys using [abc] character sets."""
        store = BasicStore()
        store.set("item_a", 1)
        store.set("item_b", 2)
        store.set("item_c", 3)
        store.set("item_d", 4)
        assert match_keys(store, "item_[ab]") == ["item_a", "item_b"]

    def test_match_all(self) -> None:
        """Match all keys with the * pattern."""
        store = BasicStore()
        store.set("a", 1)
        store.set("b", 2)
        assert match_keys(store, "*") == ["a", "b"]

    def test_no_matches(self) -> None:
        """Return an empty list when nothing matches."""
        store = BasicStore()
        store.set("key", "value")
        assert match_keys(store, "nope:*") == []

    def test_results_are_sorted(self) -> None:
        """Return results in sorted order."""
        store = BasicStore()
        store.set("c", 3)
        store.set("a", 1)
        store.set("b", 2)
        assert match_keys(store, "*") == ["a", "b", "c"]

    def test_match_is_case_sensitive(self) -> None:
        """Match case-sensitively and deterministically on every OS."""
        store = BasicStore()
        store.set("user:alice", "admin")
        store.set("User:bob", "member")
        # An uppercase pattern must not match a lowercase key.
        assert match_keys(store, "user:*") == ["user:alice"]
        assert match_keys(store, "User:*") == ["User:bob"]


class TestMatchItems:
    """Test finding key-value pairs by glob pattern."""

    def test_match_items(self) -> None:
        """Return matching key-value pairs."""
        store = BasicStore()
        store.set("user:alice", "admin")
        store.set("user:bob", "member")
        store.set("post:1", "Hello")
        result = match_items(store, "user:*")
        assert result == {"user:alice": "admin", "user:bob": "member"}

    def test_match_items_empty(self) -> None:
        """Return an empty dict when nothing matches."""
        store = BasicStore()
        store.set("key", "value")
        assert match_items(store, "nope:*") == {}


class TestCountMatches:
    """Test counting keys that match a pattern."""

    def test_count_matches(self) -> None:
        """Count matching keys."""
        store = BasicStore()
        store.set("user:alice", "admin")
        store.set("user:bob", "member")
        store.set("post:1", "Hello")
        expected_count = 2
        assert count_matches(store, "user:*") == expected_count

    def test_count_zero(self) -> None:
        """Return 0 when nothing matches."""
        store = BasicStore()
        assert count_matches(store, "anything") == 0
