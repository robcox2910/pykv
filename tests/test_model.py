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

TTLStore has no model check here: it reads the real clock
(``time.monotonic``) directly, and a model check must never sleep or depend
on wall-clock time. Giving TTLStore a clock you can pass in would make one
possible.

See ``docs/property-testing.md`` for the walk-through.
"""

import unittest
from typing import cast

import pytest
from hypothesis import strategies as st
from hypothesis.stateful import Bundle, RuleBasedStateMachine, invariant, rule

from pykv.errors import KeyNotFoundError
from pykv.store import BasicStore
from pykv.types import StorableValue

# --- Strategies: recipes for random inputs -----------------------------------

# A nested value is built from at most this many plain pieces. Hypothesis
# allows 100 by default, which makes each store slow to invent; small values
# find the same bugs, and a failure shrinks to a small value anyway.
MOST_PIECES_PER_VALUE = 10


def any_keys() -> st.SearchStrategy[str]:
    """Make any key at all: empty, spaces, emoji, accents, quotes, the lot."""
    return st.text()


def plain_values() -> st.SearchStrategy[StorableValue]:
    """Make one simple value: text, a whole number, a decimal, True/False or None."""
    return st.one_of(
        st.text(),
        st.integers(),
        # NaN ("not a number") is never equal to itself, so ``==`` could
        # never confirm the store gave it back. That's a rule of floats, not
        # of PyKV, so it's left out; infinity stays in.
        st.floats(allow_nan=False),
        st.booleans(),
        st.none(),
    )


def lists_and_dicts_of(
    children: st.SearchStrategy[object],
) -> st.SearchStrategy[list[object] | dict[str, object]]:
    """Make a list, or a dict with text keys, holding values made by ``children``."""
    return st.one_of(st.lists(children), st.dictionaries(st.text(), children))


def any_values() -> st.SearchStrategy[StorableValue]:
    """Make any value PyKV can store, including lists and dicts nested inside each other."""
    # The supported types are listed in pykv.types.StorableValue.
    return st.recursive(plain_values(), lists_and_dicts_of, max_leaves=MOST_PIECES_PER_VALUE)


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


# pytest runs this like any other test class: one run plays 100 random stories.
# (Hypothesis doesn't say what type ``TestCase`` is, so ``cast`` tells pyright.)
TestBasicStoreModel = cast("type[unittest.TestCase]", BasicStoreMachine.TestCase)
