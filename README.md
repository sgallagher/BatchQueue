# batchqueue

This module provides an extension to the basic `queue.Queue` class in order to
handle situations where incoming data for the queue tends to come in bursts to
be processed as a group.

## Example Usage:
```python3
def worker(queue=None):
    self.assertIsNotNone(queue)

    while True:
        items = queue.get_batch()
        for i in items:
            # Do stuff
            queue.task_done()

# Process a batch any time there's at least a 700ms lull in traffic
self.q = BatchQueue(lull_time=700)

# turn-on the worker thread
threading.Thread(target=worker, daemon=True, kwargs={'queue': self.q}).start()

# send ten task requests to the worker, pausing a random number of
# milliseconds (up to 1000)
for item in range(10):
    sleep(random.randrange(0, 1000) / 1000.0)
    self.q.put(item + 1)

# block until all tasks are done
self.q.join()
```
