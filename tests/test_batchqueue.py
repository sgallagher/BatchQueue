import random
import threading

from time import sleep
from batchqueue import BatchQueue
from unittest import TestCase


class Test(TestCase):
    def test_batch_queue(self):
        def worker(queue=None):
            self.assertIsNotNone(queue)

            while True:
                items = queue.get_batch()
                for i in items:
                    queue.task_done()

        # Process a batch any time there's at least a 700ms lull in traffic
        self.q = BatchQueue(lull_time=700)

        # turn-on the worker thread
        threading.Thread(target=worker, daemon=True, kwargs={"queue": self.q}).start()

        # send ten task requests to the worker, pausing a random number of
        # milliseconds (up to 1000)
        for item in range(10):
            sleep(random.randrange(0, 1000) / 1000.0)
            self.q.put(item + 1)

        # block until all tasks are done
        self.q.join()

    # Confirm that it can still function as a basic Queue
    def test_basic_queue(self):
        def worker(queue=None):
            self.assertIsNotNone(queue)

            while True:
                items = queue.get()
                queue.task_done()

        # Process a batch any time there's at least a 700ms lull in traffic
        self.q = BatchQueue(lull_time=700)

        # turn-on the worker thread
        threading.Thread(target=worker, daemon=True, kwargs={"queue": self.q}).start()

        # send ten task requests to the worker, pausing a random number of
        # milliseconds (up to 1000)
        for item in range(10):
            sleep(random.randrange(0, 1000) / 1000.0)
            self.q.put(item + 1)

        # block until all tasks are done
        self.q.join()
