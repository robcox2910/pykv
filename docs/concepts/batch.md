# Batch Operations: Working with Many Keys at Once

## The Grocery List Analogy

Imagine going to the grocery store. You could make a separate trip for each item -- one trip for milk, another for bread, another for eggs. That would be exhausting!

Instead, you write a **grocery list** and grab everything in one trip. Batch operations work the same way: instead of calling `set()` or `get()` one key at a time, you handle multiple keys in a single call.

## Batch Set

```python
from pykv import BasicStore, batch_set

store = BasicStore()

# Set many keys at once (like filling your cart from a list)
batch_set(store, {
    "player": "Alice",
    "score": 9001,
    "level": 42,
    "health": 100,
})
```

## Batch Get

```python
from pykv import batch_get

# Get many keys at once
result = batch_get(store, ["player", "score", "level"])
# {"player": "Alice", "score": 9001, "level": 42}
```

If a key is missing, you get an error. To skip missing keys instead:

```python
result = batch_get(store, ["player", "nonexistent"], skip_missing=True)
# {"player": "Alice"}  (missing key silently skipped)
```

## Batch Delete

```python
from pykv import batch_delete

# Delete many keys at once
deleted = batch_delete(store, ["score", "level", "ghost"])
print(deleted)  # 2 (only 2 keys actually existed)
```

## Batch Exists

```python
from pykv import batch_exists

result = batch_exists(store, ["player", "health", "ghost"])
# {"player": True, "health": True, "ghost": False}
```

## When to Use Batch Operations

- Loading initial data into the store
- Saving/restoring a group of related settings
- Cleaning up a group of temporary keys
- Checking which keys exist before processing
