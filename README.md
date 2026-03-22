# PyKV

An educational key-value store built from scratch in Python.

Part of the [PyLearn](https://github.com/robcox2910) series — learning computer science by building real tools.

## What Is a Key-Value Store?

Think of a **phonebook**: you look up a name (the *key*) and get back a phone number (the *value*). A key-value store works the same way — it's the simplest kind of database.

## Features

- **Get / Set / Delete** — basic phonebook operations
- **TTL (Time-To-Live)** — keys that expire, like milk with a use-by date
- **Multiple Data Types** — store strings, numbers, lists, and dicts
- **Persistence** — save to disk so data survives a restart
- **Namespaces** — group keys like folders in a filing cabinet
- **Batch Operations** — handle many keys at once, like a grocery list
- **Atomic Counters** — thread-safe increment/decrement, like a tally counter
- **Pattern Matching** — find keys matching a glob pattern

## Quick Start

```python
from pykv.store import BasicStore

store = BasicStore()
store.set("greeting", "hello")
print(store.get("greeting"))  # "hello"
```

## Related Projects

| Project | What It Teaches |
|---------|----------------|
| [PyOS](https://github.com/robcox2910/py-os) | Operating systems |
| [Pebble](https://github.com/robcox2910/pebble-lang) | Compilers & VMs |
| [PyDB](https://github.com/robcox2910/pydb) | Relational databases & SQL |
| [PyWeb](https://github.com/robcox2910/pyweb) | HTTP & web servers |
| [PyGit](https://github.com/robcox2910/pygit) | Version control |
| [PyCrypt](https://github.com/robcox2910/pycrypt) | Cryptography |
| [PyNet](https://github.com/robcox2910/pynet) | Networking & protocols |
| [PySearch](https://github.com/robcox2910/pysearch) | Full-text search |
| [PyMQ](https://github.com/robcox2910/pymq) | Message queues |
| [PyStack](https://github.com/robcox2910/pystack) | Unified platform |
