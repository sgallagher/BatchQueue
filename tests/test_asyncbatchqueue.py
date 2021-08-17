import random
import asyncio
import logging
from datetime import datetime

from batchqueue import AsyncBatchQueue
from unittest import TestCase

SAMPLES = 10
prev = datetime.now()


class Test(TestCase):
    def test_batch_queue(self):
        async def producer(queue=None):
            self.assertIsNotNone(queue)

            # send SAMPLES task requests to the worker, pausing a random number of
            # milliseconds (up to 1000)
            for item in range(SAMPLES):
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

                if i == SAMPLES:
                    break

        async def main():
            global prev
            prev = datetime.now()

            # Process a batch any time there's at least a 700ms lull in traffic
            self.q = AsyncBatchQueue(lull_time=700)

            await asyncio.gather(producer(self.q), consumer(self.q))

        asyncio.run(main(), debug=True)

    # Confirm that it can still function as a basic Queue
    def test_basic_queue(self):
        finished = False

        async def producer(queue=None):
            self.assertIsNotNone(queue)

            # send SAMPLES task requests to the worker, pausing a random number of
            # milliseconds (up to 1000)
            for item in range(SAMPLES):
                await asyncio.sleep(random.randrange(0, 1000) / 1000.0)
                await self.q.put(item + 1)

        async def consumer(queue=None):
            self.assertIsNotNone(queue)

            while True:
                try:
                    item = await queue.get()
                except asyncio.queues.QueueEmpty:
                    await asyncio.sleep(0.01)
                    continue

                queue.task_done()

                if item == SAMPLES:
                    break

        async def main():
            # Process a batch any time there's at least a 700ms lull in traffic
            self.q = AsyncBatchQueue(lull_time=700)

            await asyncio.gather(producer(self.q), consumer(self.q))

        asyncio.run(main(), debug=True)
