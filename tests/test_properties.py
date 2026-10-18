"""Property-based tests -- rules that must hold for *every* input.

An ordinary test checks one example someone thought of: "save a store
holding ``name -> Alice``, load it back, and ``name`` is still Alice". A
property test states a rule instead, such as "whatever is in the store,
loading the save file gives back exactly that", and lets Hypothesis invent
hundreds of stores to try to break it. If one breaks the rule, Hypothesis
*shrinks* it down to the smallest input that still fails, and shows you that.

Each test below says its rule in plain English in its docstring. The
strategies at the top are recipes for making random inputs; each one is
named for what it makes.

The step-by-step check of ``BasicStore`` against a plain dict lives in
``tests/test_model.py``. See ``docs/property-testing.md`` for the walk-through.
"""

import json
import tempfile
from pathlib import Path

from hypothesis import given
from hypothesis import strategies as st

from pykv.errors import PersistenceError
from pykv.persistence import load_store, save_store
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
        # NaN ("not a number") is never equal to itself, not even to a copy
        # of itself, so ``==`` could never confirm it came back. That's a
        # rule of floats, not of PyKV, so it's left out; infinity stays in.
        st.floats(allow_nan=False),
        st.booleans(),
        st.none(),
    )


def lists_and_dicts_of(
    children: st.SearchStrategy[object],
) -> st.SearchStrategy[list[object] | dict[str, object]]:
    """Make a list, or a dict with text keys, holding values made by ``children``."""
    return st.one_of(
        st.lists(children),
        st.dictionaries(st.text(), children),
    )


def any_values() -> st.SearchStrategy[StorableValue]:
    """Make any value PyKV can store, including lists and dicts nested inside each other."""
    # The supported types are listed in pykv.types.StorableValue.
    return st.recursive(plain_values(), lists_and_dicts_of, max_leaves=MOST_PIECES_PER_VALUE)


def store_contents() -> st.SearchStrategy[dict[str, StorableValue]]:
    """Make everything one store might hold: any keys, each with any value."""
    return st.dictionaries(any_keys(), any_values())


def any_bytes() -> st.SearchStrategy[bytes]:
    """Make any run of raw bytes, including the empty one and ones that aren't text."""
    return st.binary()


def json_containers_of(children: st.SearchStrategy[object]) -> st.SearchStrategy[object]:
    """Make a JSON list, or a JSON object with text keys, holding ``children``."""
    return st.one_of(st.lists(children), st.dictionaries(st.text(), children))


def any_json() -> st.SearchStrategy[object]:
    """Make any JSON document at all, whether or not it looks like a saved store."""
    return st.recursive(
        st.one_of(st.none(), st.booleans(), st.integers(), st.floats(), st.text()),
        json_containers_of,
        max_leaves=MOST_PIECES_PER_VALUE,
    )


# --- Helpers -----------------------------------------------------------------


def store_holding(contents: dict[str, StorableValue]) -> BasicStore:
    """Return a new BasicStore with every key in ``contents`` set to its value."""
    store = BasicStore()
    for key, value in contents.items():
        store.set(key, value)
    return store


def load_or_refuse(path: Path) -> BasicStore | None:
    """Load the store at ``path``, or return None if PyKV refuses it with PersistenceError.

    Any *other* exception is not caught, so it escapes and fails the test.
    """
    try:
        return load_store(path)
    except PersistenceError:
        return None


# --- Save and load: the photo of your puzzle is the whole puzzle --------------


@given(contents=store_contents())
def test_save_then_load_gives_back_the_same_store(contents: dict[str, StorableValue]) -> None:
    """Loading a saved store gives back exactly the same keys, values and types."""
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "store.json"
        save_store(store_holding(contents), path)
        loaded = load_store(path).to_dict()
    assert loaded == contents
    # ``==`` thinks True == 1 == 1.0, so also check each value kept its type.
    assert {key: type(value) for key, value in loaded.items()} == {
        key: type(value) for key, value in contents.items()
    }


# --- Loading junk: a bad save file is refused, never a crash ------------------


@given(junk=any_bytes())
def test_any_bytes_on_disk_load_or_raise_persistence_error(junk: bytes) -> None:
    """Whatever bytes are in the file, loading gives a store or a PersistenceError, never another error."""
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "store.json"
        path.write_bytes(junk)
        loaded = load_or_refuse(path)
    assert loaded is None or isinstance(loaded, BasicStore)


@given(document=any_json())
def test_any_json_on_disk_load_or_raise_persistence_error(document: object) -> None:
    """Whatever JSON is in the file, loading gives a store or a PersistenceError, never another error."""
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "store.json"
        path.write_text(json.dumps(document), encoding="utf-8")
        loaded = load_or_refuse(path)
    assert loaded is None or isinstance(loaded, BasicStore)
