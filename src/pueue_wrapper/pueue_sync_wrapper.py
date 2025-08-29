import asyncio
import threading
from pueue_wrapper.pueue_wrapper import PueueWrapper
from pueue_wrapper.models.status import PueueStatus
from pueue_wrapper.models.logs import PueueLogResponse, TaskLogEntry
from typing import Optional, Any, List


# Synchronous wrapper class
class PueueWrapperSync:
    def __init__(self):
        self.pueue_wrapper = PueueWrapper()

    def _run_async_method(self, method: str, *args) -> Any:
        """
        A helper method to run async methods synchronously.
        Handles both cases where an event loop is already running and when it's not.
        """
        async_method = getattr(self.pueue_wrapper, method)

        try:
            # Try to get the current event loop
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No event loop running, safe to use asyncio.run()
            return asyncio.run(async_method(*args))

        # Event loop is already running, we need to run in a separate thread
        def run_in_thread():
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            try:
                return new_loop.run_until_complete(async_method(*args))
            finally:
                new_loop.close()

        # Run in a separate thread to avoid event loop conflicts
        import concurrent.futures

        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_thread)
            return future.result()

    def add_task(self, command: str, label: Optional[str] = None) -> str:
        """
        Adds a task to the Pueue queue synchronously.
        """
        return self._run_async_method("add_task", command, label)

    def wait_for_task(self, task_id: str) -> str:
        """
        Waits for a specific task to finish synchronously.
        """
        return self._run_async_method("wait_for_task", task_id)

    def subscribe_to_task(self, task_id: str) -> str:
        """
        Subscribes to a task and notifies when it's done synchronously.
        """
        return self._run_async_method("subscribe_to_task", task_id)

    def submit_and_wait(self, command: str, label: Optional[str] = None) -> str:
        """
        Submit a new task and subscribe to it for completion notification synchronously.
        """
        return self._run_async_method("submit_and_wait", command, label)

    def get_status(self) -> PueueStatus:
        """
        Retrieves the status of all tasks synchronously.
        """
        return self._run_async_method("get_status")

    def get_log(self, task_id: str) -> str:
        """
        Retrieves the log of a specific task synchronously.
        """
        return self._run_async_method("get_log", task_id)

    def submit_and_wait_and_get_output(
        self, command: str, label: Optional[str] = None
    ) -> str:
        """
        Submit a task, wait for completion, and return the task output synchronously.

        Args:
            command: The command to execute
            label: Optional label for the task

        Returns:
            str: The stdout output from the task
        """
        return self._run_async_method("submit_and_wait_and_get_output", command, label)

    def get_logs_json(self, task_ids: Optional[List[str]] = None) -> PueueLogResponse:
        """
        Retrieves the logs of all tasks or specific tasks in JSON format synchronously.

        Args:
            task_ids: Optional list of task IDs to retrieve. If None, gets all tasks.

        Returns:
            PueueLogResponse: Structured log data for all requested tasks
        """
        return self._run_async_method("get_logs_json", task_ids)

    def get_task_log_entry(self, task_id: str) -> Optional[TaskLogEntry]:
        """
        Retrieves a single task's log entry with structured data synchronously.

        Args:
            task_id: The ID of the task to retrieve

        Returns:
            TaskLogEntry: The structured log entry for the task, or None if not found
        """
        return self._run_async_method("get_task_log_entry", task_id)


def _test_sync_functions():
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
    def get_status_sync() -> str:
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
    # https://chatgpt.com/share/67e65261-05c0-8012-a492-7bf13d425736

    _test_sync_functions()

    pueue_sync = PueueWrapperSync()

    from loguru import logger

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
