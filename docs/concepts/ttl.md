# TTL: Time-To-Live

## The Milk Expiration Date Analogy

When you buy milk from the store, it has a date printed on it: "Best before June 1." After that date, the milk expires and you throw it away. TTL (Time-To-Live) works the same way for your data.

You can say: "Store this value, but delete it after 60 seconds." When the time runs out, the key automatically disappears -- like magic self-destructing sticky notes!

## Why Use TTL?

- **Login sessions**: "Remember me for 24 hours"
- **Caching**: "Keep this web page for 5 minutes"
- **Rate limiting**: "Allow 10 requests per minute"
- **Temporary locks**: "Lock this resource for 30 seconds"

## Using TTLStore

```python
from pykv import TTLStore

store = TTLStore()

# This key lives forever (no TTL)
store.set("permanent", "I'm here to stay")

# This key expires in 60 seconds
store.set("session", "abc123", ttl=60.0)

# This key expires in 5 seconds
store.set("temp", "going away soon", ttl=5.0)
```

## Checking Remaining Time

```python
remaining = store.ttl_remaining("session")
print(f"Session expires in {remaining:.1f} seconds")  # e.g., "58.3 seconds"

# Keys without TTL return None
store.ttl_remaining("permanent")  # None (lives forever)
```

## What Happens When a Key Expires?

```python
import time

store.set("flash", "now you see me", ttl=1.0)
store.get("flash")          # "now you see me"

time.sleep(2)               # Wait for expiration...

store.get("flash")          # Raises KeyExpiredError!
store.exists("flash")       # False
```

The expired key is cleaned up automatically -- like the milk being thrown away.

### Expired vs. never existed

PyKV tells you *why* a lookup failed with two different errors:

- **`KeyNotFoundError`** -- the key was never set (like asking for a carton you never bought).
- **`KeyExpiredError`** -- the key existed but its timer ran out (like reaching for milk that is past its date).

Both are subclasses of `PyKVError`, so you can catch either one with `except PyKVError`, or handle them separately:

```python
from pykv.errors import KeyExpiredError, KeyNotFoundError

try:
    value = store.get("session")
except KeyExpiredError:
    print("Your session timed out -- please log in again.")
except KeyNotFoundError:
    print("No such session.")
```

Both `get` and `ttl_remaining` follow this rule.

## Refreshing TTL

You can reset the timer by setting the key again:

```python
store.set("session", "abc123", ttl=60.0)
# ... 30 seconds later, user is still active ...
store.set("session", "abc123", ttl=60.0)  # Timer resets to 60 seconds
```
