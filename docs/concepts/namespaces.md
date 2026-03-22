# Namespaces: Organizing Keys

## The Filing Cabinet Analogy

Imagine a giant filing cabinet at school. Instead of throwing all papers into one big pile, you organize them into labeled folders:

```
📁 math:homework1
📁 math:homework2
📁 science:lab_report
📁 science:quiz
📁 english:essay
```

The folder name (`math:`, `science:`, `english:`) is the **namespace**. It keeps things organized so that `math:homework1` and `english:homework1` don't get mixed up.

## Creating a Namespace

```python
from pykv import BasicStore, Namespace

store = BasicStore()

# Create namespaces (like labeled folders)
users = Namespace(store, "users:")
posts = Namespace(store, "posts:")
```

## Using Namespaces

```python
# Store data through the namespace
users.set("alice", {"role": "admin"})
users.set("bob", {"role": "member"})
posts.set("1", "Hello, world!")

# Retrieve data -- you only need the short key
users.get("alice")    # {"role": "admin"}
posts.get("1")        # "Hello, world!"
```

Behind the scenes, the keys in the store are:

```
users:alice  →  {"role": "admin"}
users:bob    →  {"role": "member"}
posts:1      →  "Hello, world!"
```

## Listing Keys in a Namespace

```python
users.keys()   # ["alice", "bob"]   (prefix is removed!)
posts.keys()   # ["1"]
```

## Isolation

Namespaces keep groups separate. Clearing one namespace doesn't touch others:

```python
users.clear()
users.size()    # 0
posts.size()    # 1 (still there!)
```

## Why Use Namespaces?

When multiple parts of your program share one store, namespaces prevent key collisions:

```python
# Without namespaces: DANGER! Keys collide!
store.set("count", 42)       # Game module
store.set("count", 7)        # Chat module -- oops, overwrote game data!

# With namespaces: Safe!
game = Namespace(store, "game:")
chat = Namespace(store, "chat:")
game.set("count", 42)
chat.set("count", 7)         # No collision!
```
