from concurrent.futures import ProcessPoolExecutor
import unittest
import asyncio
from unittest.mock import patch

from app.process_pool import SyncExecutor, run_sync_in_executor


# Standalone synchronous functions that can be pickled
def sync_function(x, y):
    return x + y


def another_sync_function(x):
    return x * 2


class TestSyncExecutor(unittest.TestCase):
    def test_sync_function_in_executor(self):
        wrapped_sync_function = run_sync_in_executor()(sync_function)
        result = asyncio.run(wrapped_sync_function(5, 10))
        self.assertEqual(result, 15)

    def test_another_sync_function_in_executor(self):
        wrapped_another_sync_function = run_sync_in_executor()(another_sync_function)
        result = asyncio.run(wrapped_another_sync_function(3))
        self.assertEqual(result, 6)

    @patch.object(SyncExecutor, "get_instance", wraps=SyncExecutor.get_instance)
    def test_executor_is_shared_across_calls(self, mock_get_instance):
        wrapped_sync_function = run_sync_in_executor()(sync_function)
        wrapped_another_sync_function = run_sync_in_executor()(another_sync_function)

        result1 = asyncio.run(wrapped_sync_function(5, 10))
        result2 = asyncio.run(wrapped_another_sync_function(3))

        self.assertEqual(result1, 15)
        self.assertEqual(result2, 6)

        # Check if the same executor instance is returned both times
        instance1 = mock_get_instance()
        instance2 = mock_get_instance()

        self.assertIs(
            instance1,
            instance2,
            "The same executor instance should be used across calls",
        )

    @patch.object(ProcessPoolExecutor, "shutdown")
    def test_executor_shutdown(self, mock_shutdown):
        wrapped_sync_function = run_sync_in_executor()(sync_function)
        asyncio.run(wrapped_sync_function(2, 3))

        # Manually trigger shutdown and verify
        executor_instance = SyncExecutor.get_instance()
        executor_instance.shutdown()

        mock_shutdown.assert_called_once()


if __name__ == "__main__":
    unittest.main()
