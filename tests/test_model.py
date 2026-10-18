"""Model check -- BasicStore must behave exactly like a plain Python dict.

A property test checks one rule for many inputs. A *model check* goes
further: Hypothesis invents a random *story* -- set this, delete that, read
the other, clear everything -- and plays it on two things at once:

- the real ``BasicStore``;
- a **model**: a plain ``dict``, which we already trust to be right.

After every step the two must agree. If they ever disagree, Hypothesis
shrinks the story to the shortest list of steps that still goes wrong.

The model is deliberately *not* a copy of ``BasicStore``'s code. It is the
simplest thing that is obviously correct, so when the two disagree, the
store is the one to suspect.

A second machine does the same for ``Namespace``: three folders in one
store (``users``, ``users:admin`` nested inside it, and ``posts``) against
a dict of dicts, one inner dict per folder. Folders must never share a key.

TTLStore has no model check here: it reads the real clock
(``time.monotonic``) directly, and a model check must never sleep or depend
on wall-clock time. Giving TTLStore a clock you can pass in would make one
possible.

See ``docs/property-testing.md`` for the walk-through.
"""

import unittest
from typing import cast

import pytest
from hypothesis import settings
from hypothesis import strategies as st
from hypothesis.stateful import Bundle, RuleBasedStateMachine, invariant, rule

from pykv.errors import KeyNotFoundError, NamespaceError
from pykv.namespace import Namespace
from pykv.store import BasicStore
from pykv.types import StorableValue
from tests.strategies import any_keys, any_values, keys_with_separator, namespace_keys

# --- The machine: one story, played on the store and on a dict ----------------


class BasicStoreMachine(RuleBasedStateMachine):
    """Play random sets, deletes, reads and clears on a BasicStore and a dict side by side."""

    # Keys we've used before. Brand-new random keys almost never repeat, so
    # rules also pick from here to read, overwrite or delete a key that
    # really is (or was) in the store.
    keys = Bundle("keys")

    def __init__(self) -> None:
        """Start with an empty store and an empty dict."""
        super().__init__()
        self.store = BasicStore()
        self.model: dict[str, StorableValue] = {}

    @rule(target=keys, key=any_keys(), value=any_values())
    def set_new_key(self, key: str, value: StorableValue) -> str:
        """Set a fresh key in both, and remember it for later steps."""
        self.store.set(key, value)
        self.model[key] = value
        return key

    @rule(key=keys, value=any_values())
    def overwrite_key(self, key: str, value: StorableValue) -> None:
        """Set a key we've used before to a new value, in both."""
        self.store.set(key, value)
        self.model[key] = value

    @rule(key=st.one_of(keys, any_keys()))
    def delete_key(self, key: str) -> None:
        """Delete a key from both; the store says True exactly when the key was there."""
        was_there = key in self.model
        self.model.pop(key, None)
        assert self.store.delete(key) == was_there

    @rule(key=st.one_of(keys, any_keys()))
    def get_key(self, key: str) -> None:
        """Read a key: the store gives the dict's value, or KeyNotFoundError if the dict has none."""
        assert self.store.exists(key) == (key in self.model)
        if key in self.model:
            assert self.store.get(key) == self.model[key]
        else:
            with pytest.raises(KeyNotFoundError):
                self.store.get(key)

    @rule(key=st.one_of(keys, any_keys()), default=any_values())
    def get_key_or_default(self, key: str, default: StorableValue) -> None:
        """Read a key with a fallback: the store answers just like ``dict.get``."""
        assert self.store.get_or_default(key, default) == self.model.get(key, default)

    @rule()
    def clear(self) -> None:
        """Empty both."""
        self.store.clear()
        self.model.clear()

    @invariant()
    def same_keys_and_values(self) -> None:
        """After every step, the store holds exactly the dict's keys and values."""
        assert self.store.size() == len(self.model)
        assert sorted(self.store.keys()) == sorted(self.model)
        assert all(self.store.exists(key) for key in self.model)
        assert self.store.to_dict() == self.model


# why: 20 steps find the same bugs; 50 (the default) is most of the run time
BasicStoreMachine.TestCase.settings = settings(stateful_step_count=20)
# pytest runs this like any other test class: one run plays 100 random stories.
# (Hypothesis doesn't say what type ``TestCase`` is, so ``cast`` tells pyright.)
TestBasicStoreModel = cast("type[unittest.TestCase]", BasicStoreMachine.TestCase)


# --- Namespaces: three folders in one store, played against a dict of dicts ---

# Each folder's name, and how it is spelled when it's made. "users:" and
# "posts" check that a trailing ":" is optional; "users:admin" sits inside
# "users", which is exactly where folders used to overlap.
FOLDERS = {"users": "users:", "users:admin": "users:admin", "posts": "posts"}


def folder_names() -> st.SearchStrategy[str]:
    """Pick one of the three folders."""
    return st.sampled_from(sorted(FOLDERS))


class NamespaceMachine(RuleBasedStateMachine):
    """Play random steps on three namespaces sharing one store, and on a dict of dicts."""

    keys = Bundle("keys")

    def __init__(self) -> None:
        """Start with an empty store, three namespaces on it, and three empty dicts."""
        super().__init__()
        self.store = BasicStore()
        self.folders = {name: Namespace(self.store, spelling) for name, spelling in FOLDERS.items()}
        self.model: dict[str, dict[str, StorableValue]] = {name: {} for name in FOLDERS}

    @rule(target=keys, name=folder_names(), key=namespace_keys(), value=any_values())
    def set_new_key(self, name: str, key: str, value: StorableValue) -> str:
        """Set a fresh key in one folder, and remember it for later steps."""
        self.folders[name].set(key, value)
        self.model[name][key] = value
        return key

    @rule(name=folder_names(), key=keys, value=any_values())
    def overwrite_key(self, name: str, key: str, value: StorableValue) -> None:
        """Set a key we've used before (maybe in another folder) to a new value."""
        self.folders[name].set(key, value)
        self.model[name][key] = value

    @rule(name=folder_names(), key=st.one_of(keys, namespace_keys()))
    def delete_key(self, name: str, key: str) -> None:
        """Delete a key from one folder; it says True exactly when the key was there."""
        was_there = key in self.model[name]
        self.model[name].pop(key, None)
        assert self.folders[name].delete(key) == was_there

    @rule(name=folder_names(), key=st.one_of(keys, namespace_keys()))
    def get_key(self, name: str, key: str) -> None:
        """Read a key from one folder: its value, or KeyNotFoundError if that folder has none."""
        folder = self.folders[name]
        assert folder.exists(key) == (key in self.model[name])
        if key in self.model[name]:
            assert folder.get(key) == self.model[name][key]
        else:
            with pytest.raises(KeyNotFoundError):
                folder.get(key)

    @rule(name=folder_names(), key=st.one_of(keys, namespace_keys()), default=any_values())
    def get_key_or_default(self, name: str, key: str, default: StorableValue) -> None:
        """Read a key with a fallback: the folder answers just like ``dict.get``."""
        assert self.folders[name].get_or_default(key, default) == self.model[name].get(key, default)

    @rule(name=folder_names(), key=keys_with_separator(), value=any_values())
    def refuse_key_with_separator(self, name: str, key: str, value: StorableValue) -> None:
        """Refuse a key containing ":" -- it could land in another folder."""
        with pytest.raises(NamespaceError):
            self.folders[name].set(key, value)

    @rule(name=folder_names(), key=keys_with_separator())
    def refuse_separator_on_reads_and_deletes(self, name: str, key: str) -> None:
        """Refuse a key containing ":" on get, get_or_default, exists and delete too."""
        folder = self.folders[name]
        for method in (folder.get, folder.get_or_default, folder.exists, folder.delete):
            with pytest.raises(NamespaceError):
                method(key)

    @rule(name=folder_names())
    def clear(self, name: str) -> None:
        """Empty one folder, and only that folder."""
        self.folders[name].clear()
        self.model[name].clear()

    @invariant()
    def every_folder_matches_its_dict(self) -> None:
        """After every step, each folder holds exactly its own dict's keys and values."""
        for name, folder in self.folders.items():
            expected = self.model[name]
            assert folder.size() == len(expected)
            assert sorted(folder.keys()) == sorted(expected)
            assert all(folder.get(key) == value for key, value in expected.items())
        # The folders are the only things in the store, so no key is shared.
        assert self.store.size() == sum(len(expected) for expected in self.model.values())


# why: 20 steps find the same bugs; 50 (the default) is most of the run time
NamespaceMachine.TestCase.settings = settings(stateful_step_count=20)
# pytest runs this like any other test class: one run plays 100 random stories.
TestNamespaceModel = cast("type[unittest.TestCase]", NamespaceMachine.TestCase)
