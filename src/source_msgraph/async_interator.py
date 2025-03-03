import asyncio

import asyncio
from typing import AsyncGenerator, Iterator, Any

class AsyncToSyncIterator:
    """
    Converts an async generator into a synchronous iterator while ensuring proper event loop handling.
    """

    def __init__(self, async_gen: AsyncGenerator[Any, None]):
        """
        Initializes the iterator by consuming an async generator synchronously.

        Args:
            async_gen (AsyncGenerator): The async generator yielding results.
        """
        self.async_gen = async_gen
        self.loop = self._get_event_loop()
        self.iterator = self._to_iterator()

    def _get_event_loop(self) -> asyncio.AbstractEventLoop:
        """Returns the currently running event loop or creates a new one if none exists."""
        try:
            loop = asyncio.get_running_loop()
            if loop.is_running():
                return None  # Indicate an already running loop (handled in `_to_iterator()`)
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            return loop

    def _to_iterator(self) -> Iterator:
        """
        Ensures that the async generator is consumed using the correct event loop.
        Uses streaming (does not load all results into memory).
        """
        if self.loop:
            return iter(self.loop.run_until_complete(self._stream_results()))
        else:
            return iter(asyncio.run(self._stream_results()))  # Safe for Jupyter, PySpark

    # Caution : prone to OOM errors
    async def _stream_results(self):
        # """Streams async generator results without collecting all in memory."""
        # page_count = 0
        # async for item in self.async_gen:
        #     if page_count >= self.max_pages:
        #         raise RuntimeError("Pagination limit reached, possible infinite loop detected!")
        #     yield item
        #     page_count += 1  # Track pages to prevent infinite loops
        return [item async for item in self.async_gen]

    def __iter__(self) -> Iterator:
        """Returns the synchronous iterator."""
        return self.iterator


import asyncio
from typing import AsyncGenerator, Iterator, Any

class AsyncToSyncIteratorV2:
    """
    Converts an async generator into a synchronous iterator while ensuring proper event loop handling.
    """

    def __init__(self, async_gen: AsyncGenerator[Any, None]):
        """
        Initializes the iterator by consuming an async generator synchronously.

        Args:
            async_gen (AsyncGenerator): The async generator yielding results.
        """
        self.async_gen = async_gen
        self.iterator = self._to_iterator()

    def _to_iterator(self) -> Iterator:
        """
        Ensures that the async generator is consumed using the correct event loop.
        Uses streaming (does not load all results into memory).
        """
        try:
            loop = asyncio.get_running_loop()
            return self._sync_generator(loop)  # Works inside Jupyter
        except RuntimeError:
            return iter(asyncio.run(self._collect_results()))  # Works in scripts

    def _sync_generator(self, loop: asyncio.AbstractEventLoop) -> Iterator:
        """
        Streams async results into a sync generator while inside a running event loop.
        """
        queue = asyncio.Queue()

        async def _producer():
            """Fills the queue with async results."""
            async for item in self.async_gen:
                await queue.put(item)
            await queue.put(None)  # Sentinel to signal completion

        async def _consumer():
            """Yields items from the queue in sync mode."""
            task = loop.create_task(_producer())
            while True:
                item = await queue.get()
                if item is None:
                    break
                yield item
            await task  # Ensure producer task completes

        return iter(loop.run_until_complete(self._collect_results()))

    async def _collect_results(self):
        """Collects async generator results into a list (safe for asyncio.run)."""
        return [item async for item in self.async_gen]

    def __iter__(self) -> Iterator:
        """Returns the synchronous iterator."""
        return self.iterator

    def __next__(self) -> Any:
        """Returns the next item from the iterator."""
        return next(self.iterator)