# Pattern Matching: Finding Keys

## The File Search Analogy

When you search for files on your computer, you can use wildcards:

- `*.txt` finds all text files
- `photo_?.jpg` finds `photo_1.jpg`, `photo_2.jpg`, etc.
- `report_[abc].pdf` finds `report_a.pdf`, `report_b.pdf`, `report_c.pdf`

PyKV uses the same glob patterns to search through your keys!

## Wildcard Reference

| Pattern | Meaning | Example |
|---------|---------|---------|
| `*` | Match anything (zero or more characters) | `user:*` matches `user:alice`, `user:bob` |
| `?` | Match exactly one character | `log?` matches `log1`, `logA`, not `log10` |
| `[abc]` | Match one of the listed characters | `item_[12]` matches `item_1`, `item_2` |

## Finding Keys

```python
from pykv import BasicStore, match_keys

store = BasicStore()
store.set("user:alice", "admin")
store.set("user:bob", "member")
store.set("post:1", "Hello!")
store.set("post:2", "World!")

# Find all user keys
match_keys(store, "user:*")    # ["user:alice", "user:bob"]

# Find all post keys
match_keys(store, "post:*")    # ["post:1", "post:2"]

# Find everything
match_keys(store, "*")         # ["post:1", "post:2", "user:alice", "user:bob"]
```

## Finding Keys AND Values

```python
from pykv import match_items

match_items(store, "user:*")
# {"user:alice": "admin", "user:bob": "member"}
```

## Counting Matches

```python
from pykv import count_matches

count_matches(store, "user:*")  # 2
count_matches(store, "post:*")  # 2
count_matches(store, "nope:*")  # 0
```

## Combining with Namespaces

Pattern matching works great alongside namespaces for powerful data organization:

```python
from pykv import BasicStore, Namespace, match_keys

store = BasicStore()
cache = Namespace(store, "cache:")
cache.set("page:home", "<html>...")
cache.set("page:about", "<html>...")
cache.set("api:users", "[...]")

# Find all cached pages
match_keys(store, "cache:page:*")  # ["cache:page:about", "cache:page:home"]
```
