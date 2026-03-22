"""Tests for AtomicCounter -- thread-safe increment and decrement."""

import threading

import pytest

from pykv.counters import AtomicCounter
from pykv.store import BasicStore


class TestAtomicCounterBasics:
    """Test basic increment and decrement operations."""

    def test_increment_new_key(self) -> None:
        """Increment a key that does not exist yet (starts at 0)."""
        store = BasicStore()
        counter = AtomicCounter(store)
        assert counter.increment("visitors") == 1

    def test_increment_existing_key(self) -> None:
        """Increment a key that already has a value."""
        store = BasicStore()
        counter = AtomicCounter(store)
        counter.increment("visitors")
        expected_value = 2
        assert counter.increment("visitors") == expected_value

    def test_increment_by_amount(self) -> None:
        """Increment by a custom amount."""
        store = BasicStore()
        counter = AtomicCounter(store)
        expected_value = 5
        assert counter.increment("score", amount=5) == expected_value

    def test_decrement_new_key(self) -> None:
        """Decrement a key that does not exist (goes to -1)."""
        store = BasicStore()
        counter = AtomicCounter(store)
        assert counter.decrement("balance") == -1

    def test_decrement_existing_key(self) -> None:
        """Decrement from an existing value."""
        store = BasicStore()
        counter = AtomicCounter(store)
        counter.increment("visitors")
        counter.increment("visitors")
        assert counter.decrement("visitors") == 1

    def test_decrement_by_amount(self) -> None:
        """Decrement by a custom amount."""
        store = BasicStore()
        counter = AtomicCounter(store)
        counter.increment("score", amount=10)
        expected_value = 7
        assert counter.decrement("score", amount=3) == expected_value


class TestAtomicCounterGetAndReset:
    """Test getting and resetting counter values."""

    def test_get_value_existing(self) -> None:
        """Get the current value of an existing counter."""
        store = BasicStore()
        counter = AtomicCounter(store)
        counter.increment("hits")
        assert counter.get_value("hits") == 1

    def test_get_value_missing(self) -> None:
        """Get 0 for a counter that does not exist."""
        store = BasicStore()
        counter = AtomicCounter(store)
        assert counter.get_value("ghost") == 0

    def test_reset_counter(self) -> None:
        """Reset a counter to zero."""
        store = BasicStore()
        counter = AtomicCounter(store)
        counter.increment("hits", amount=10)
        counter.reset("hits")
        assert counter.get_value("hits") == 0


class TestAtomicCounterTypeError:
    """Test error handling when a key holds a non-integer value."""

    def test_increment_non_int_raises(self) -> None:
        """Raise TypeError when incrementing a non-integer key."""
        store = BasicStore()
        store.set("name", "Alice")
        counter = AtomicCounter(store)
        with pytest.raises(TypeError, match="not an int"):
            counter.increment("name")


class TestAtomicCounterThreadSafety:
    """Test thread safety of atomic counters."""

    def test_concurrent_increments(self) -> None:
        """Handle concurrent increments correctly."""
        store = BasicStore()
        counter = AtomicCounter(store)
        iterations = 100
        num_threads = 4

        def incrementer() -> None:
            for _ in range(iterations):
                counter.increment("counter")

        threads = [threading.Thread(target=incrementer) for _ in range(num_threads)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        expected_total = 400
        assert counter.get_value("counter") == expected_total
