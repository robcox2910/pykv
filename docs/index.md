# What is a Key-Value Store?

## The Phonebook Analogy

Imagine you have a phonebook. You look up someone's **name** (the key) and find their **phone number** (the value). That's exactly what a key-value store does -- it lets you store pieces of information and look them up by name, super fast.

```
Name (Key)      →  Phone Number (Value)
─────────────────────────────────────────
"Alice"         →  "555-0101"
"Bob"           →  "555-0202"
"Charlie"       →  "555-0303"
```

## Why Do We Need Key-Value Stores?

In the real world, key-value stores power some of the biggest apps:

- **Gaming**: Store player scores, inventory, and session data
- **Social media**: Cache user profiles so pages load instantly
- **Shopping**: Keep track of what's in your cart
- **Chat apps**: Store who's online right now

They're incredibly fast because looking up a key is like opening a book directly to the right page -- you don't have to read every page to find what you want.

## What Can PyKV Do?

PyKV is your own key-value store, built from scratch! Here's what you'll learn:

| Feature | What It Does | Real-World Example |
|---------|-------------|-------------------|
| **BasicStore** | Store and retrieve data | A phonebook |
| **TTL** | Data that expires | Milk with an expiration date |
| **Namespaces** | Organize keys into groups | Folders in a filing cabinet |
| **Batch Ops** | Work with many keys at once | A grocery shopping list |
| **Counters** | Thread-safe counting | A tally/click counter |
| **Patterns** | Search for keys by pattern | Finding files on your computer |
| **Persistence** | Save to disk | Writing in your notebook |

## Quick Start

```python
from pykv import BasicStore

# Create a new store
store = BasicStore()

# Store some data
store.set("player_name", "Alice")
store.set("high_score", 9001)
store.set("inventory", ["sword", "shield", "potion"])

# Look it up later
print(store.get("player_name"))   # "Alice"
print(store.get("high_score"))    # 9001
print(store.get("inventory"))     # ["sword", "shield", "potion"]
```

## Next Steps

Ready to dive deeper? Check out the concepts:

1. [Basics](concepts/basics.md) -- Get, Set, Delete
2. [TTL](concepts/ttl.md) -- Expiration times
3. [Types](concepts/types.md) -- Different data types
4. [Persistence](concepts/persistence.md) -- Saving to disk
5. [Namespaces](concepts/namespaces.md) -- Organizing keys
6. [Batch Operations](concepts/batch.md) -- Working with many keys
7. [Counters](concepts/counters.md) -- Thread-safe counting
8. [Patterns](concepts/patterns.md) -- Searching for keys
