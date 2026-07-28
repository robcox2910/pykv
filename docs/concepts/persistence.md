# Persistence: Saving to Disk

## The Notebook Analogy

Imagine you're working on a jigsaw puzzle all afternoon. When it's time for dinner, you take a photo of your progress so you can pick up exactly where you left off tomorrow. That's what persistence does -- it saves your key-value store to a file so nothing is lost when your program stops.

Without persistence, your data lives only in memory (RAM). When the program ends, poof -- everything disappears, like a dream you can't remember.

## Saving Your Store

```python
from pykv import BasicStore, save_store

store = BasicStore()
store.set("player", "Alice")
store.set("score", 9001)
store.set("inventory", ["sword", "potion"])

# Save everything to a file
save_store(store, "game_save.json")
```

This creates a JSON file you can even open in a text editor:

```json
{
  "player": {"type": "str", "data": "Alice"},
  "score": {"type": "int", "data": 9001},
  "inventory": {"type": "list", "data": ["sword", "potion"]}
}
```

## Loading Your Store

```python
from pykv import load_store

# Load everything back
store = load_store("game_save.json")

print(store.get("player"))     # "Alice"
print(store.get("score"))      # 9001
print(store.get("inventory"))  # ["sword", "potion"]
```

## Error Handling

Things can go wrong with files. PyKV gives you clear errors:

```python
from pykv import load_store
from pykv.errors import PersistenceError

try:
    store = load_store("missing_file.json")
except PersistenceError as e:
    print(f"Oops: {e}")  # "Failed to load store from missing_file.json: ..."
```

## What About TTLStore?

Persistence only works with a `BasicStore`. If you try to `save_store` a
`TTLStore`, you get a clear `PersistenceError` instead of silently losing
your expiration timers:

```python
from pykv import TTLStore, save_store
from pykv.errors import PersistenceError

ttl_store = TTLStore()
ttl_store.set("session", "abc123", ttl=60.0)

try:
    save_store(ttl_store, "session.json")
except PersistenceError as e:
    print(e)  # Cannot save a TTLStore: its expiration timers cannot be persisted...
```

Why not just save the values? Because a TTL timer measures time from *right
now* using a clock that resets when your program restarts. Saving the timer
to disk would be meaningless after a restart, so PyKV refuses rather than
quietly saving the values and dropping every timer.

Teaching a TTLStore to save and restore its timers -- by writing down the
*seconds remaining* for each key and recounting them on load -- is a great
exercise to try yourself!

## Tips

- **Save often**: Call `save_store` after important changes
- **Use meaningful filenames**: `user_data.json` is better than `data.json`
- **JSON is human-readable**: You can inspect your saved data with any text editor
