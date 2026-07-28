# Data Types

## The Backpack Analogy

Imagine a backpack where you can store different things:

| Python Type | Analogy | Example |
|-------------|---------|---------|
| `str` | A book (text) | `"Hello, world!"` |
| `int` | A calculator showing a whole number | `42` |
| `float` | A calculator showing a decimal | `3.14` |
| `bool` | A light switch (on/off) | `True` or `False` |
| `None` | An empty pocket | `None` |
| `list` | A shopping list | `["milk", "bread"]` |
| `dict` | A mini-phonebook | `{"name": "Alice"}` |

## Storing Different Types

Unlike some key-value stores that only handle strings, PyKV can store all these types natively:

```python
from pykv import BasicStore

store = BasicStore()

store.set("name", "Alice")                    # string
store.set("age", 13)                          # integer
store.set("gpa", 3.95)                        # float
store.set("enrolled", True)                   # boolean
store.set("nickname", None)                   # None
store.set("hobbies", ["coding", "gaming"])    # list
store.set("grades", {"math": 95, "sci": 88}) # dictionary
```

## Serialization: How Values Get Saved

When you save your store to disk, each value is wrapped in a labeled box:

```json
{
  "name": {"type": "str", "data": "Alice"},
  "age": {"type": "int", "data": 13}
}
```

The "type" label tells PyKV how to unpack the value later -- like writing "FRAGILE" on a shipping box so the delivery person knows to handle it carefully.

## What You Cannot Store

PyKV supports the most common types. You cannot store:

- Custom objects (like your own classes)
- Sets
- Tuples (use lists instead)
- Functions

If you try, you'll get a `SerializationError` with a helpful message explaining what went wrong.

### One honest catch: coercion happens *inside* lists and dicts

The `SerializationError` only guards the **top-level** value. Because saving
round-trips your value through JSON, unsupported types *nested inside* a list
or dict are quietly converted instead of rejected:

```python
store.set("point", (1, 2))          # top-level tuple -> SerializationError (blocked)

store.set("points", [(1, 2), (3, 4)])  # tuples inside a list -> saved as [[1, 2], [3, 4]]
store.set("scores", {1: "a", 2: "b"})  # int dict keys -> saved as {"1": "a", "2": "b"}
```

So "you cannot store tuples" is true for a tuple you store directly, but a
tuple tucked inside a list becomes a list, and non-string dict keys become
strings. JSON simply has no tuples and only allows string keys. When in
doubt, use lists and string keys from the start so what you load back is
exactly what you saved.
