"""Tests for persistence -- saving and loading stores to disk."""

from pathlib import Path

import pytest

from pykv.errors import PersistenceError
from pykv.persistence import load_store, save_store
from pykv.store import BasicStore

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

    def test_save_accepts_string_path(self, tmp_path: Path) -> None:
        """Accept a string path instead of a Path object."""
        store = BasicStore()
        store.set("key", "value")
        filepath = str(tmp_path / "string_path.json")
        save_store(store, filepath)
        loaded = load_store(filepath)
        assert loaded.get("key") == "value"


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
