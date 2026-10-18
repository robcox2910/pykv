"""Strategies -- recipes for random keys and values, shared by the property tests.

A strategy tells Hypothesis how to invent one kind of input. Each one here
is a named function, named for what it makes, with a one-line docstring.
``tests/test_properties.py`` and ``tests/test_model.py`` both use them.
"""

from hypothesis import strategies as st

from pykv.types import StorableValue

# A nested value is built from at most this many plain pieces. Hypothesis
# allows 100 by default, which makes each store slow to invent; small values
# find the same bugs, and a failure shrinks to a small value anyway.
MOST_PIECES_PER_VALUE = 10


def any_keys() -> st.SearchStrategy[str]:
    """Make any key at all: empty, spaces, emoji, accents, quotes, the lot."""
    return st.text()


def namespace_keys() -> st.SearchStrategy[str]:
    """Make any key a namespace accepts: any text at all, except the ``:`` separator."""
    return st.text(alphabet=st.characters(exclude_characters=":"))


def keys_with_separator() -> st.SearchStrategy[str]:
    """Make a key a namespace must refuse: any text with at least one ``:`` in it."""
    return st.lists(st.text(), min_size=2).map(":".join)


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
    return st.one_of(st.lists(children), st.dictionaries(st.text(), children))


def any_values() -> st.SearchStrategy[StorableValue]:
    """Make any value PyKV can store, including lists and dicts nested inside each other."""
    # The supported types are listed in pykv.types.StorableValue.
    return st.recursive(plain_values(), lists_and_dicts_of, max_leaves=MOST_PIECES_PER_VALUE)
