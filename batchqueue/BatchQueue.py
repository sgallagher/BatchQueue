import queue
import threading

from time import monotonic as time
from time import sleep

VERSION = "0.1.0"


class BatchQueue(queue.Queue):
    """Variant of a queue that can return a batch of objects when there is
    a lull in their addition.

    :lull_time How long in milliseconds for there to be no activity on the
    BatchQueue before signaling that a batch is ready.

    The queue will pass all of its contents to self.callback when lull_time
    seconds have passed without a new entry on the queue.

    Note that in order for the lull_time to work, each instance of
    BatchQueue will create a thread.
    """

    def __init__(self, lull_time=1000):
        super().__init__()
        self.lull_time = lull_time / 1000.0
        self.modified = 0
        self.batch_count = 0
        self.batch_ready = threading.Condition(self.mutex)

        # Create thread to announce batches
        threading.Thread(target=self._announcer, daemon=True).start()

    def _announcer(self):
        while True:
            # Check whether the modified time is older than lull_time
            now = time()
            with self.batch_ready:
                if (now - self.modified) >= self.lull_time:
                    # Save the current count of entries in the
                    self.batch_count = self._qsize()
                    self.batch_ready.notify()
            sleep(0.01)

    def put(self, item, block=True, timeout=None):
        """Put an item into the queue.

        If optional args 'block' is true and 'timeout' is None (the default),
        block if necessary until a free slot is available. If 'timeout' is
        a non-negative number, it blocks at most 'timeout' seconds and raises
        the Full exception if no free slot was available within that time.
        Otherwise ('block' is false), put an item on the queue if a free slot
        is immediately available, else raise the Full exception ('timeout'
        is ignored in that case).
        """
        with self.not_full:
            if self.maxsize > 0:
                if not block:
                    if self._qsize() >= self.maxsize:
                        raise queue.Full
                elif timeout is None:
                    while self._qsize() >= self.maxsize:
                        self.not_full.wait()
                elif timeout < 0:
                    raise ValueError("'timeout' must be a non-negative number")
                else:
                    endtime = time() + timeout
                    while self._qsize() >= self.maxsize:
                        remaining = endtime - time()
                        if remaining <= 0.0:
                            raise queue.Full
                        self.not_full.wait(remaining)
            self._put(item)
            self.modified = time()
            self.unfinished_tasks += 1
            self.not_empty.notify()

    def get(self, block=True, timeout=None):
        """Remove and return an item from the queue.

        If optional args 'block' is true and 'timeout' is None (the default),
        block if necessary until an item is available. If 'timeout' is
        a non-negative number, it blocks at most 'timeout' seconds and raises
        the Empty exception if no item was available within that time.
        Otherwise ('block' is false), return an item if one is immediately
        available, else raise the Empty exception ('timeout' is ignored
        in that case).
        """
        with self.not_empty:
            if not block:
                if not self._qsize():
                    raise queue.Empty
            elif timeout is None:
                while not self._qsize():
                    self.not_empty.wait()
            elif timeout < 0:
                raise ValueError("'timeout' must be a non-negative number")
            else:
                endtime = time() + timeout
                while not self._qsize():
                    remaining = endtime - time()
                    if remaining <= 0.0:
                        raise queue.Empty
                    self.not_empty.wait(remaining)
            item = self._get()
            # Decrease the batch_count so we don't get try to read too many
            # entries.
            self.batch_count -= 1

            self.modified = time()
            self.not_full.notify()
            return item

    def get_batch(self, block=True, timeout=None):
        """Remove and return an item from the queue.

        If optional args 'block' is true and 'timeout' is None (the default),
        block if necessary until an item is available. If 'timeout' is
        a non-negative number, it blocks at most 'timeout' seconds and raises
        the Empty exception if no item was available within that time.
        Otherwise ('block' is false), return an item if one is immediately
        available, else raise the Empty exception ('timeout' is ignored
        in that case).
        """
        with self.batch_ready:
            if not block:
                if not self._qsize():
                    raise queue.Empty
            elif timeout is None:
                while not self._qsize():
                    self.batch_ready.wait()
            elif timeout < 0:
                raise ValueError("'timeout' must be a non-negative number")
            else:
                endtime = time() + timeout
                while not self._qsize():
                    remaining = endtime - time()
                    if remaining <= 0.0:
                        raise queue.Empty
                    self.batch_ready.wait(remaining)

            items = list()
            while self.queue:
                items.append(self._get())

            self.modified = time()
            self.not_full.notify()
            return items
