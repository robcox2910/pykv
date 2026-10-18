"""Tests for persistence -- saving and loading stores to disk."""

import os
from pathlib import Path

import pytest

from pykv.errors import PersistenceError
from pykv.persistence import load_store, save_store
from pykv.store import BasicStore
from pykv.ttl import TTLStore

EXPECTED_AGE = 13
EXPECTED_INT = 42


class TestSaveStore:
    """Test saving a store to a JSON file."""

    def test_save_creates_file(self, tmp_path: Path) -> None:
        """Create a JSON file on disk."""
        store = BasicStore()
        store.set("name", "Alice")
        filepath = tmp_path / "data.json"
        save_store(store, filepath)
        assert filepath.exists()

    def test_save_creates_parent_dirs(self, tmp_path: Path) -> None:
        """Create parent directories if they do not exist."""
        store = BasicStore()
        store.set("key", "value")
        filepath = tmp_path / "nested" / "deep" / "data.json"
        save_store(store, filepath)
        assert filepath.exists()

    def test_save_empty_store(self, tmp_path: Path) -> None:
        """Save an empty store without errors."""
        store = BasicStore()
        filepath = tmp_path / "empty.json"
        save_store(store, filepath)
        assert filepath.exists()


class TestLoadStore:
    """Test loading a store from a JSON file."""

    def test_load_restores_data(self, tmp_path: Path) -> None:
        """Load a store and verify all data is restored."""
        store = BasicStore()
        store.set("name", "Alice")
        store.set("age", 13)
        store.set("colors", ["red", "blue"])
        filepath = tmp_path / "data.json"
        save_store(store, filepath)

        loaded = load_store(filepath)
        assert loaded.get("name") == "Alice"
        assert loaded.get("age") == EXPECTED_AGE
        assert loaded.get("colors") == ["red", "blue"]

    def test_load_missing_file_raises(self, tmp_path: Path) -> None:
        """Raise PersistenceError when the file does not exist."""
        filepath = tmp_path / "missing.json"
        with pytest.raises(PersistenceError, match="Failed to load"):
            load_store(filepath)

    def test_load_invalid_json_raises(self, tmp_path: Path) -> None:
        """Raise PersistenceError when the file contains invalid JSON."""
        filepath = tmp_path / "bad.json"
        filepath.write_text("not json at all!", encoding="utf-8")
        with pytest.raises(PersistenceError, match="Invalid JSON"):
            load_store(filepath)

    def test_load_file_that_is_not_utf8_text_raises(self, tmp_path: Path) -> None:
        """Raise PersistenceError naming the file when it isn't UTF-8 text.

        Regression: found by a property test, which shrank it to one byte.
        """
        filepath = tmp_path / "not_text.json"
        filepath.write_bytes(b"\x80")
        with pytest.raises(PersistenceError, match=r"not_text\.json"):
            load_store(filepath)

    def test_save_accepts_string_path(self, tmp_path: Path) -> None:
        """Accept a string path instead of a Path object."""
        store = BasicStore()
        store.set("key", "value")
        filepath = str(tmp_path / "string_path.json")
        save_store(store, filepath)
        loaded = load_store(filepath)
        assert loaded.get("key") == "value"


class TestSaveTTLStore:
    """Test that saving a TTLStore is rejected instead of losing TTLs."""

    def test_save_ttl_store_raises(self, tmp_path: Path) -> None:
        """Raise PersistenceError rather than silently dropping timers."""
        store = TTLStore()
        store.set("session", "abc123", ttl=60.0)
        filepath = tmp_path / "ttl.json"
        with pytest.raises(PersistenceError, match="Cannot save a TTLStore"):
            save_store(store, filepath)

    def test_save_ttl_store_does_not_create_file(self, tmp_path: Path) -> None:
        """Reject the TTLStore before writing anything to disk."""
        store = TTLStore()
        store.set("key", "value")
        filepath = tmp_path / "ttl.json"
        with pytest.raises(PersistenceError):
            save_store(store, filepath)
        assert not filepath.exists()


class TestRoundTrip:
    """Test saving and loading preserves all data types."""

    def test_round_trip_all_types(self, tmp_path: Path) -> None:
        """Save and load a store with all supported data types."""
        store = BasicStore()
        store.set("string", "hello")
        store.set("int", 42)
        store.set("float", 3.14)
        store.set("bool", True)
        store.set("none", None)
        store.set("list", [1, 2, 3])
        store.set("dict", {"a": 1})

        filepath = tmp_path / "all_types.json"
        save_store(store, filepath)
        loaded = load_store(filepath)

        assert loaded.get("string") == "hello"
        assert loaded.get("int") == EXPECTED_INT
        assert loaded.get("float") == pytest.approx(3.14)
        assert loaded.get("bool") is True
        assert loaded.get("none") is None
        assert loaded.get("list") == [1, 2, 3]
        assert loaded.get("dict") == {"a": 1}


class _SimulatedCrashError(OSError):
    """Stands in for the power going out part-way through a save."""


def test_interrupted_save_keeps_the_previous_file(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Regression: a crash mid-save used to leave a truncated, unloadable file."""
    store = BasicStore()
    store.set("k", "old")
    path = tmp_path / "data.json"
    save_store(store, path)
    before = path.read_bytes()
    store.set("k", "new")

    def write_half_then_crash(self: Path, data: str, *_args: object, **_kwargs: object) -> int:
        with self.open("w", encoding="utf-8") as handle:
            handle.write(data[: len(data) // 2])
        raise _SimulatedCrashError

    def crash(*_args: object) -> None:
        raise _SimulatedCrashError

    monkeypatch.setattr(Path, "write_text", write_half_then_crash)
    monkeypatch.setattr(os, "replace", crash)
    with pytest.raises((OSError, PersistenceError)):
        save_store(store, path)
    monkeypatch.undo()
    assert path.read_bytes() == before
    load_store(path)
    assert [p.name for p in tmp_path.iterdir()] == ["data.json"]


WRONG_SHAPES = ["[]", '{"a": 1}', '{"a": {"no": "type"}}']


class TestWrongShapeFiles:
    """Valid JSON that isn't a saved store is refused, never loaded as empty."""

    @pytest.mark.parametrize("content", WRONG_SHAPES)
    def test_wrong_shape_raises_persistence_error_naming_the_file(
        self, tmp_path: Path, content: str
    ) -> None:
        """Loading it raises PersistenceError with the file name, so it can't be overwritten."""
        path = tmp_path / "saved.json"
        path.write_text(content, encoding="utf-8")
        with pytest.raises(PersistenceError, match=r"saved\.json"):
            load_store(path)
