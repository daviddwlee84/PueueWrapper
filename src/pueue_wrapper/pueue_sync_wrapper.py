import asyncio
from pueue_wrapper.pueue_wrapper import PueueWrapper
from pueue_wrapper.models.status import PueueStatus
from typing import Optional


# Synchronous wrapper class
class PueueWrapperSync:
    def __init__(self):
        self.pueue_wrapper = PueueWrapper()

    def _run_async_method(self, method: str, *args) -> str:
        """
        A helper method to run async methods synchronously.
        """
        return asyncio.run(getattr(self.pueue_wrapper, method)(*args))

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
