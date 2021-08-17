import asyncio


class AsyncBatchQueue(asyncio.Queue):
    """Variant of a queue that can return a batch of objects when there is
    a lull in their addition.

    :lull_time How long in milliseconds for there to be no activity on the
    BatchQueue before signaling that a batch is ready.
    """

    def __init__(self, maxsize=0, lull_time=1000):
        super().__init__(maxsize)
        self.lull_time = lull_time / 1000.0
        self.lull_task = None
        self._reschedule_lull_task()

    def _reschedule_lull_task(self):
        if self.lull_task:
            self.lull_task.cancel()
        self.lull_task = asyncio.create_task(asyncio.sleep(self.lull_time))

    async def put(self, item, block=True, timeout=None):
        """Put an item into the queue.

        If optional args 'block' is true and 'timeout' is None (the default),
        block if necessary until a free slot is available. If 'timeout' is
        a non-negative number, it blocks at most 'timeout' seconds and raises
        the Full exception if no free slot was available within that time.
        Otherwise ('block' is false), put an item on the queue if a free slot
        is immediately available, else raise the Full exception ('timeout'
        is ignored in that case).
        """
        if block and timeout:
            await asyncio.wait_for(super().put(item, timeout))
        elif block and timeout is None:
            await super().put(item)
        else:
            self.put_nowait(item)

        self._reschedule_lull_task()

    async def get_batch(self, block=True, timeout=None):
        """Remove and return a batch of items from the queue.

        If optional args 'block' is true and 'timeout' is None (the default),
        block if necessary until an item is available. If 'timeout' is
        a non-negative number, it blocks at most 'timeout' seconds and raises
        the Empty exception if no item was available within that time.
        Otherwise ('block' is false), return a batch if one is immediately
        available, else raise the Empty exception ('timeout' is ignored
        in that case).
        """
        if not block:
            if not self.qsize():
                raise asyncio.queues.QueueEmpty

        while True:
            try:
                await asyncio.wait_for(asyncio.shield(self.lull_task), timeout)
            except asyncio.TimeoutError:
                raise asyncio.queues.QueueEmpty
            except asyncio.CancelledError:
                # Timer was reset, wait again
                pass

            # We waited successfully
            break

        items = list()
        while self._queue:
            items.append(self._get())

        return items
