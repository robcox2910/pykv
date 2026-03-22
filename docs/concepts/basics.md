# Basics: Get, Set, Delete

## The Notebook Analogy

A `BasicStore` is like a notebook where you write labels and information:

- **Set** = Write a new entry (or erase and rewrite an existing one)
- **Get** = Look up an entry by its label
- **Delete** = Erase an entry
- **Exists** = Check if a label is in the notebook (without reading it)
- **Keys** = List every label in the notebook

## Creating a Store

```python
from pykv import BasicStore

store = BasicStore()
```

That's it! You now have an empty notebook ready to use.

## Setting Values

```python
store.set("name", "Alice")
store.set("age", 13)
store.set("favorite_colors", ["blue", "green"])
```

If you set a key that already exists, the old value is replaced:

```python
store.set("name", "Alice")
store.set("name", "Bob")     # Overwrites "Alice"
store.get("name")             # "Bob"
```

## Getting Values

```python
name = store.get("name")     # "Bob"
```

If the key doesn't exist, you get an error:

```python
store.get("nonexistent")     # Raises KeyNotFoundError!
```

To avoid the error, use `get_or_default`:

```python
store.get_or_default("nickname", "N/A")  # "N/A" (no error)
```

## Deleting Values

```python
store.delete("name")          # Returns True (it existed)
store.delete("name")          # Returns False (already gone)
```

## Checking Existence

```python
store.exists("age")           # True
store.exists("ghost")         # False
```

## Other Useful Methods

```python
store.keys()    # List all key names: ["age", "favorite_colors"]
store.size()    # How many entries: 2
store.clear()   # Erase everything
store.size()    # 0
```
