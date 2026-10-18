# Property Testing (Every Ticket Gets Its Coat Back)

## The Coat Check Inspector

Picture the coat check at a theatre. You hand over your coat, you get a
ticket, and at the end of the night the ticket gets you your coat back.
It's a key-value store made of coat hangers: the ticket is the **key**,
the coat is the **value**.

How would you check the coat check works? The usual way: hand in one
coat, take your ticket, get the coat back, and smile. That's an
**example test**. It's useful, but it only tells you about the one coat
you thought of.

Now imagine an inspector. All evening they hand in thousands of things --
coats, a single glove, an umbrella, a scarf with a name tag in Japanese,
a ticket numbered zero, nothing at all -- and for each one they check a
single rule:

> Whatever you hand in, the same ticket gets exactly that thing back.

That rule is a **property**. It doesn't say what any one coat looks
like. It says something that must be true for *every* coat.

When the inspector finds something that breaks the rule, they don't just
report "something went wrong around 9 o'clock, with a heap of stuff".
They try again with less and less -- fewer things, smaller things,
simpler tickets -- checking it still goes wrong each time, until it's as
simple as it can be. That boiling-down is called **shrinking**, and it's
the best part: the smallest failing input usually points straight at
the bug.

In Python, the inspector is a library called
[Hypothesis](https://hypothesis.readthedocs.io/). PyKV's property tests
live in `tests/test_properties.py`, next to the ordinary example tests,
and the model check (more on that below) is in `tests/test_model.py`.

## A Property from PyKV

PyKV can [save a store to disk and load it again](concepts/persistence.md).
That's a coat check across time: whatever you save, loading should give
back. Here's the property:

```python
def any_keys() -> st.SearchStrategy[str]:
    """Make any key at all: empty, spaces, emoji, accents, quotes, the lot."""
    return st.text()


def store_contents() -> st.SearchStrategy[dict[str, StorableValue]]:
    """Make everything one store might hold: any keys, each with any value."""
    return st.dictionaries(any_keys(), any_values())


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
```

Line by line:

- **`any_keys()` and `store_contents()`** are **strategies**: recipes
  for making random inputs. `st.text()` makes any string at all,
  including the empty string, `" "`, `"🍕"` and `"Zoë's \"key\""`.
  `store_contents()` makes a whole dictionary of keys and values;
  `any_values()` (in the test file) makes any value PyKV can store:
  text, numbers, `True`/`False`, `None`, and lists and dicts nested
  inside each other. Each one is a named function so the test reads like
  a sentence.
- **`@given(contents=store_contents())`** tells Hypothesis to run the
  test many times (100 in a normal run), each time with a fresh `contents`.
- **The docstring** says the rule in plain English. If you can't say the
  rule in one sentence, it probably isn't a good property yet.
- **`tempfile.TemporaryDirectory()`** gives each run its own empty
  folder, which is deleted afterwards.
- **`store_holding(contents)`** is a small helper that makes a
  `BasicStore` and calls `set` for every key.
- **The first `assert`** is the rule itself: save it, load it, and you
  must get back exactly what you put in. This kind of property is called
  a **round-trip**.
- **The second `assert`** is there because Python thinks `True == 1`
  and `1 == 1.0`. Without it, a store that saved `True` and loaded `1`
  would pass. A good property says exactly what "the same" means.

Notice what the test *doesn't* say. It never says "save `name -> Alice`
and you get `Alice`". It doesn't need to know any answers. It only needs
a rule that's always true.

PyKV has two more properties, about loading a file that *isn't* a good
save file:

| Rule | Test |
|---|---|
| Whatever bytes are in the file, loading gives a store or a `PersistenceError`, never another error | `test_any_bytes_on_disk_load_or_raise_persistence_error` |
| Whatever JSON is in the file, loading gives a store or a `PersistenceError`, never another error | `test_any_json_on_disk_load_or_raise_persistence_error` |

Why do they matter? Because a program using PyKV writes
`except PersistenceError:` to handle a broken save file. If some other
error sneaks out, that program crashes instead.

There's a catch, though. A `load_store` that refuses **every** file
passes both of those, because refusing is always allowed. **The "junk"
properties alone are passed by a loader that does nothing**, so the
round-trip sits beside them: it fails straight away if loading never
gives anything back.

## Checking Against a Model

A property checks one action. But a store is something you change step
by step: set, set again, delete, read, clear. Bugs often hide in the
*order* of steps -- deleting a key you never set, or setting the same key
twice.

So the inspector has a second trick. They carry a little notebook and
write down every ticket and coat by hand. After every single step at the
counter, they compare the racks with the notebook. If the racks ever
disagree with the notebook, something's wrong with the coat check.

That notebook is a **model**: something simple that we already trust.
For `BasicStore`, the model is a plain Python `dict`. Here's the start of
the check in `tests/test_model.py`:

```python
class BasicStoreMachine(RuleBasedStateMachine):
    """Play random sets, deletes, reads and clears on a BasicStore and a dict side by side."""

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

    @rule(key=st.one_of(keys, any_keys()))
    def delete_key(self, key: str) -> None:
        """Delete a key from both; the store says True exactly when the key was there."""
        was_there = key in self.model
        self.model.pop(key, None)
        assert self.store.delete(key) == was_there

    @invariant()
    def same_keys_and_values(self) -> None:
        """After every step, the store holds exactly the dict's keys and values."""
        assert self.store.size() == len(self.model)
        assert sorted(self.store.keys()) == sorted(self.model)
        assert all(self.store.exists(key) for key in self.model)
        assert self.store.to_dict() == self.model


TestBasicStoreModel = cast("type[unittest.TestCase]", BasicStoreMachine.TestCase)
```

Piece by piece:

- **`RuleBasedStateMachine`** is Hypothesis's tool for testing things
  that change step by step. Hypothesis makes up a random **story** of
  steps and plays it.
- **`self.store` and `self.model`** are the coat racks and the notebook.
  Every story starts with both empty.
- **Each `@rule`** is one kind of step. It does the same thing to the
  store and to the dict. The real file has rules to set a new key,
  overwrite a key, delete, read with `get` and `get_or_default`, and
  clear.
- **`keys = Bundle("keys")`** is a bag of keys used earlier in the story.
  Two random strings almost never match, so without it the story would
  hardly ever overwrite or delete a key that is really there. `set_new_key`
  puts its key in the bag (`target=keys`); later rules can pull one out.
  `delete_key` picks either a key from the bag or a brand-new one, so it
  tries deleting keys that exist *and* keys that don't.
- **The `@invariant()`** runs after every single step and compares
  everything: how many keys, which keys, and every value.
- **`TestBasicStoreModel = ...TestCase`** turns the machine into a test
  that pytest can find and run. One run plays 100 random stories.

The `dict` is a good model because it's obviously right and it's *not*
`BasicStore`'s code. If we built the model by copying `BasicStore`, any
bug would be in both, and they'd agree perfectly about the wrong answer.

`TTLStore` doesn't get a model check (yet). Its keys expire using the
computer's real clock (`time.monotonic()`), and a test that has to
*wait* for keys to expire is slow and flaky. If `TTLStore` let you hand
it a pretend clock that you move forward yourself, a model check could
skip through hours in an instant. That's a good exercise to try!

## Try It Yourself

Let's break `BasicStore` on purpose and watch the inspector find it.

Open `src/pykv/store.py`, find `delete`, and change its last line, as if
you'd copied the line above by mistake:

```python
            return True  # was: return False
```

Now `delete` says "yes, I deleted it" even when the key was never there.
Run the property tests:

```bash
uv run pytest tests/test_properties.py tests/test_model.py -q --no-cov -p no:randomly
```

Hypothesis reports this (trimmed to the interesting part):

```
self = BasicStoreMachine({}), key = ''

    @rule(key=st.one_of(keys, any_keys()))
    def delete_key(self, key: str) -> None:
        """Delete a key from both; the store says True exactly when the key was there."""
        was_there = key in self.model
        self.model.pop(key, None)
>       assert self.store.delete(key) == was_there
E       AssertionError: assert True == False
E        +  where True = delete('')
E       Failing test case: <state machine>
E       state = BasicStoreMachine()
E       state.same_keys_and_values()
E       state.delete_key(key='')
E       state.teardown()
```

Read the story at the bottom like a script. Hypothesis tried long,
messy stories with dozens of sets and deletes, then shrank them all
the way down to **one step**: start empty, delete the key `''`. The
store said `True` ("deleted it!"), but the notebook knew there was
nothing to delete.

Notice that `same_keys_and_values` would never catch this bug: the
store's *contents* are still right. Only the rule that checks what
`delete` *says* catches it. That's why each rule checks its own answer as
well as the invariant checking the contents.

Put the line back to `return False` and run the tests again. They pass.

!!! tip "Older Hypothesis versions"
    Older versions of Hypothesis print `Falsifying example:` instead of
    `Failing test case:`. It means the same thing.

## A Bug We Found

When we first wrote `test_any_bytes_on_disk_load_or_raise_persistence_error`,
it failed on PyKV's real code -- no deliberate bug needed:

```
E   UnicodeDecodeError: 'utf-8' codec can't decode byte 0x80 in position 0: invalid start byte
E   Failing test case: test_any_bytes_on_disk_load_or_raise_persistence_error(
E       junk=b'\x80',
E   )
```

A save file holding **one byte**, `0x80`, made `load_store` crash with a
`UnicodeDecodeError` instead of a `PersistenceError`.

Here's why. PyKV's save files are JSON text, stored as UTF-8. In UTF-8,
the byte `0x80` can only appear *in the middle* of a character, never at
the start, so a file starting with it isn't text at all. The old code
was ready for two kinds of trouble:

```python
try:
    raw = path.read_text(encoding="utf-8")
except OSError as exc:           # the file is missing, or can't be read
    ...
try:
    serialized = json.loads(raw)
except json.JSONDecodeError as exc:   # the text isn't JSON
    ...
```

But a file that isn't text at all fails in between: Python reads the
bytes fine, then fails to *decode* them into text. That's a
`UnicodeDecodeError`, which isn't an `OSError`, so it slipped straight
past.

The example tests tried a missing file and a file of `"not json at all!"`.
Both are text. Nobody thought to try a file that isn't text at all -- a
photo saved with the wrong name, or a save file that got corrupted. The
inspector didn't need to think of it: `st.binary()` makes bytes like
that all the time.

The fix was one line:

```python
except (OSError, UnicodeDecodeError) as exc:   # was: except OSError as exc:
```

Now a file that isn't text gets the same clear `PersistenceError` as a
missing one, naming the file. The shrunk input also became an ordinary
example test in `tests/test_persistence.py`, so this bug can never sneak
back in, even if someone deletes the property.

## Run It Yourself

Run just the property tests and the model check (100 examples each, the
same every time):

```bash
uv run pytest tests/test_properties.py tests/test_model.py --no-cov
```

The `--no-cov` turns off the coverage check, which expects the *whole*
test suite to run and would fail on two files.

Run them the long way (2,000 random examples each, different every run)
to hunt for rarer bugs:

```bash
uv run pytest tests/test_properties.py tests/test_model.py --no-cov --hypothesis-profile=thorough
```

The normal run uses a fixed seed, so it tries the same inputs every time
and a passing build means the same thing on every computer. The thorough
run is random, so each time you run it the inspector brings a brand-new
pile of coats.

## Next Up

Try writing your own model check. A good place to start is
[Namespaces](concepts/namespaces.md): a namespace should behave like its
own little dict, and setting `"score"` in the `alice:` namespace should
never change `"score"` in `bob:`. What's the model? (Hint: a dict of
dicts.) Then let Hypothesis pick the prefixes too. What happens when one
prefix starts with another, like `users:` and `users:admin:`? Let the
inspector tell you.
