# batchqueue

This module provides an extension to the basic `queue.Queue` class in order to
handle situations where incoming data for the queue tends to come in bursts to
be processed as a group.

## Example Usage (BatchQueue):
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

## Example Usage (AsyncBatchQueue):
```python3
async def producer(queue=None):
    self.assertIsNotNone(queue)

    # send 10 task requests to the worker, pausing a random number of
    # milliseconds (up to 1000)
    for item in range(10):
        await asyncio.sleep(random.randrange(0, 1000) / 1000.0)
        await self.q.put(item + 1)

async def consumer(queue=None):
    self.assertIsNotNone(queue)
    global prev

    while True:
        try:
            items = await queue.get_batch(block=False)
        except asyncio.queues.QueueEmpty:
            await asyncio.sleep(0.01)
            continue

        now = datetime.now()
        lull = now - prev
        logging.info(f"Waited for {lull} seconds: {items}")
        prev = now

        for i in items:
            queue.task_done()

        if i == 10:
            break

async def main():
    global prev
    prev = datetime.now()

    # Process a batch any time there's at least a 700ms lull in traffic
    self.q = AsyncBatchQueue(lull_time=700)

    await asyncio.gather(producer(self.q), consumer(self.q))

asyncio.run(main(), debug=True)
```
