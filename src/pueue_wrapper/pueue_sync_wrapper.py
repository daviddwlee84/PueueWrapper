import asyncio
import concurrent.futures
from typing import Any
from loguru import logger
from .core.sync_core import PueueSyncCore
from .extensions.statistics import SyncStatisticsMixin
from .extensions.advanced import SyncAdvancedMixin


class PueueWrapperSync(PueueSyncCore, SyncStatisticsMixin, SyncAdvancedMixin):
    """
    Complete synchronous wrapper for Pueue with all functionality.

    This class combines the core Pueue CLI functionality with statistical analysis
    and advanced convenience methods through multiple inheritance, providing
    synchronous interfaces for all operations.
    """

    def __init__(self):
        super().__init__()
        self.logger = logger.bind(module="pueue_wrapper_sync")

    def _run_async_method(self, method: str, *args) -> Any:
        """
        A helper method to run async methods synchronously.
        Handles both cases where an event loop is already running and when it's not.

        This method is needed for the sync mixin classes to delegate to async methods.

        Args:
            method: Name of the async method to call
            *args: Arguments to pass to the method

        Returns:
            Result from the async method
        """
        # First check if this is a sync mixin method that needs to delegate to async
        if hasattr(self.async_core, method):
            async_method = getattr(self.async_core, method)
        else:
            # This should be one of the mixin methods implemented in this class hierarchy
            # Look for the async version in the mixin classes
            async_method = None
            for cls in self.__class__.__mro__:
                if hasattr(cls, method) and method != "_run_async_method":
                    # Check if this is an async method by looking for the same method
                    # in our async_core or the mixin classes used by PueueWrapper
                    from .extensions.statistics import StatisticsMixin
                    from .extensions.advanced import AdvancedMixin

                    if hasattr(StatisticsMixin, method):
                        async_method = getattr(StatisticsMixin, method)
                        break
                    elif hasattr(AdvancedMixin, method):
                        async_method = getattr(AdvancedMixin, method)
                        break

            if async_method is None:
                raise AttributeError(
                    f"Method {method} not found in async implementation"
                )

        try:
            # Try to get the current event loop
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No event loop running, safe to use asyncio.run()
            if hasattr(self.async_core, method):
                return asyncio.run(async_method(*args))
            else:
                # This is a mixin method, we need to call it on the async_core with mixins
                # Create a temporary wrapper that includes the mixins
                from .pueue_wrapper import PueueWrapper

                temp_wrapper = PueueWrapper()
                bound_method = getattr(temp_wrapper, method)
                return asyncio.run(bound_method(*args))

        # Event loop is already running, we need to run in a separate thread
        def run_in_thread():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                if hasattr(self.async_core, method):
                    return new_loop.run_until_complete(async_method(*args))
                else:
                    # This is a mixin method
                    from .pueue_wrapper import PueueWrapper

                    temp_wrapper = PueueWrapper()
                    bound_method = getattr(temp_wrapper, method)
                    return new_loop.run_until_complete(bound_method(*args))
            finally:
                new_loop.close()

        # Run in a separate thread to avoid event loop conflicts
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_thread)
            return future.result()


def _test_sync_functions():
    """Test function using basic sync operations without the wrapper class."""
    from .pueue_wrapper import PueueWrapper

    # Synchronous function to add task and wait
    def add_task_sync(command: str) -> str:
        pueue = PueueWrapper()
        return asyncio.run(pueue.add_task(command))

    # Synchronous function to submit a task and wait
    def submit_and_wait_sync(command: str) -> str:
        pueue = PueueWrapper()
        return asyncio.run(pueue.submit_and_wait(command))

    # Synchronous function to get log
    def get_log_sync(task_id: str) -> str:
        pueue = PueueWrapper()
        return asyncio.run(pueue.get_log(task_id))

    # Synchronous function to get status
    def get_status_sync():
        pueue = PueueWrapper()
        return asyncio.run(pueue.get_status())

    task_id = submit_and_wait_sync('echo "Hello, Pueue!"')
    print(f"Task {task_id} completed.")

    status = get_status_sync()
    print(f"Current status: {status}")

    log = get_log_sync(task_id)
    print(f"Log: {log}")


# Example usage
if __name__ == "__main__":
    # Test basic sync functions first
    _test_sync_functions()

    # Test the full sync wrapper
    pueue_sync = PueueWrapperSync()

    # Submit a task and wait for it synchronously
    task_id = pueue_sync.submit_and_wait('echo "Hello, Pueue!"')
    logger.info(pueue_sync.get_log(task_id))

    # You can submit and monitor multiple tasks synchronously
    pueue_sync.submit_and_wait("sleep 3", "Sleep 3 seconds")
    pueue_sync.submit_and_wait("sleep 5")

    # Get structured status
    status = pueue_sync.get_status()
    task_ids = list(status.tasks.keys())
    logger.info(f"Tasks: {task_ids}")
    logger.info(f"Default group status: {status.groups['default'].status}")

    # Log details about the first task if any exist
    if task_ids:
        first_task = status.tasks[task_ids[0]]
        logger.info(f"First task command: {first_task.command}")
        # Get the status type (e.g., "Done", "Running") and its info
        status_type = next(iter(first_task.status))
        status_info = first_task.status[status_type]
        logger.info(f"First task status: {status_type}, result: {status_info.result}")

        # Test statistics functionality
        logger.info("=== Testing statistics functionality ===")

        group_stats = pueue_sync.get_group_statistics("default")
        logger.info(f"Group 'default' statistics:")
        logger.info(f"  Total tasks: {group_stats.total_tasks}")
        logger.info(f"  Completed: {group_stats.completed_tasks}")
        logger.info(f"  Success rate: {group_stats.success_rate:.2%}")
