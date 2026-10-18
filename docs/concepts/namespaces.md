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

The folder name (`math`, `science`, `english`) is the **namespace**. The `:` between the folder name and the paper name is the **separator**. It keeps things organized so that `math:homework1` and `english:homework1` don't get mixed up.

## Creating a Namespace

```python
from pykv import BasicStore, Namespace

store = BasicStore()

# Create namespaces (like labeled folders)
users = Namespace(store, "users")
posts = Namespace(store, "posts")
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

The `:` is added for you. You can write it yourself if you like --
`Namespace(store, "users:")` is exactly the same folder as
`Namespace(store, "users")`.

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
game = Namespace(store, "game")
chat = Namespace(store, "chat")
game.set("count", 42)
chat.set("count", 7)         # No collision!
```

## Folders Inside Folders

A folder can sit inside another folder. Use `:` in the namespace's
*name* to nest it:

```python
users = Namespace(store, "users")
admins = Namespace(store, "users:admin")   # a folder inside "users"

users.set("bob", {"role": "member"})
admins.set("alice", {"role": "admin"})
```

In the store, that's:

```
users:bob          →  {"role": "member"}
users:admin:alice  →  {"role": "admin"}
```

Each folder only sees its own papers. The `admin` folder inside `users`
is a separate folder, so `users` doesn't count what's inside it:

```python
users.keys()    # ["bob"]     (not "admin:alice"!)
admins.keys()   # ["alice"]
users.clear()   # empties "users" -- "users:admin" keeps alice
```

## The Separator Rule

There is one rule that makes all of this work:

> **A key inside a namespace can never contain `:`.**

Here's why. Suppose the rule didn't exist, and the `users` folder filed
a paper called `"admin:alice"`. Its full label would be
`users:` + `admin:alice` = `users:admin:alice`. But that's exactly the
label of `alice` in the `users:admin` folder! Two folders would be
sharing one paper, and writing in one would scribble over the other.

**Two folders must never share a paper.** With the rule, they can't:
the folder is always everything before the *last* `:`, and the paper
name is everything after it. Every label in the store belongs to exactly
one folder.

So PyKV refuses a key with `:` in it and tells you why:

```python
from pykv import NamespaceError

users.set("admin:alice", 1)
# NamespaceError: Key 'admin:alice' contains ':', which separates folder names ...
```

If you wanted a folder inside `users`, make a nested namespace instead,
like `Namespace(store, "users:admin")` above.

A namespace's name can't be empty, either, and every part of it between
`:`s needs at least one character. `Namespace(store, "")`,
`Namespace(store, ":")` and `Namespace(store, "users::admin")` all raise
`NamespaceError`.

`NamespaceError` is a `PyKVError`, so `except PyKVError:` catches it too.

## Upgrading from 0.2

Two things work differently since v0.3.0, and neither one raises an error, so watch out:

- The `:` is now always added for you. A prefix written without one, like `Namespace(store, "cache_")`, now files `x` as `cache_:x` instead of `cache_x`.
- An old key with `:` in it, like `users:admin:alice` written through the `users` namespace, now belongs to the nested `users:admin` folder. The `users` folder's `keys()`, `size()` and `clear()` skip it; use `Namespace(store, "users:admin")` to reach it.
