import asyncio
from concurrent.futures import ProcessPoolExecutor

import functools
import inspect


# Define a top-level function to handle the sync function execution
def execute_sync(func, *args, **kwargs):
    return func(*args, **kwargs)


# Ensure the process pool executor is a singleton
class SyncExecutor:
    def __init__(self, max_workers=5):
        self.executor = ProcessPoolExecutor(max_workers=max_workers)

    async def run_in_executor(self, func, *args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            self.executor, functools.partial(execute_sync, func, *args, **kwargs)
        )

    def shutdown(self):
        self.executor.shutdown(wait=True)

    @classmethod
    def get_instance(cls, max_workers=5):
        if not hasattr(cls, "_instance"):
            cls._instance = cls(max_workers=max_workers)
        return cls._instance


# Factory function to create decorators for running functions in the executor
def run_sync_in_executor():
    executor = SyncExecutor()

    def decorator(func):
        async def wrapper(*args, **kwargs):
            if not inspect.iscoroutinefunction(func):
                return await executor.run_in_executor(func, *args, **kwargs)
            else:
                return await func(*args, **kwargs)

        return wrapper

    return decorator


# # def handle_exit(signum, frame):
# #     executor_instance = SyncExecutor.get_instance()
# #     executor_instance.shutdown()
# #     print("Executor shutdown")
# #     exit(0)


# # signal.signal(signal.SIGINT, handle_exit)
# # signal.signal(signal.SIGTERM, handle_exit)
