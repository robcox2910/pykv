# Atomic Counters: Thread-Safe Counting

## The Tally Counter Analogy

Have you seen those clicky tally counters that bouncers use to count people entering a venue? Every click adds exactly 1 to the count. Even if two bouncers click at the exact same time, the counter never gets confused -- each click is a single, unbreakable action.

That's what "atomic" means in programming: an operation that cannot be interrupted or corrupted, even when multiple things happen at the same time.

## The Problem Without Atomic Operations

Imagine two threads (workers) both trying to increment the same counter:

```
Counter = 5

Thread A reads: 5          Thread B reads: 5
Thread A writes: 6         Thread B writes: 6  (should be 7!)
```

Both threads read 5 and wrote 6, so we lost an increment! The counter should be 7 but it's only 6. This is called a **race condition**.

## Using AtomicCounter

```python
from pykv import BasicStore, AtomicCounter

store = BasicStore()
counter = AtomicCounter(store)

# Increment (starts at 0 if the key doesn't exist)
counter.increment("visitors")     # Returns 1
counter.increment("visitors")     # Returns 2
counter.increment("visitors", 5)  # Returns 7 (add 5 at once)

# Decrement
counter.decrement("visitors")     # Returns 6
counter.decrement("visitors", 3)  # Returns 3

# Check current value
counter.get_value("visitors")     # 3

# Reset to zero
counter.reset("visitors")
counter.get_value("visitors")     # 0
```

## Thread Safety

AtomicCounter uses a lock internally, so multiple threads can safely increment/decrement the same counter without race conditions:

```python
import threading

counter = AtomicCounter(BasicStore())

def count_clicks():
    for _ in range(1000):
        counter.increment("clicks")

# Run 4 threads simultaneously
threads = [threading.Thread(target=count_clicks) for _ in range(4)]
for t in threads:
    t.start()
for t in threads:
    t.join()

print(counter.get_value("clicks"))  # Always exactly 4000!
```

## Use Cases

- **Page view counters**: Track how many times a page is visited
- **Rate limiting**: Count requests per minute
- **Game scores**: Safely update scores from multiple sources
- **Inventory**: Track stock levels with concurrent updates
