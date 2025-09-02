from typing import Optional
from loguru import logger


class AdvancedMixin:
    """
    Mixin class providing advanced functionality built on top of core Pueue operations.

    This mixin adds convenience methods that combine multiple core operations
    to provide higher-level task management capabilities.
    """

    async def subscribe_to_task(self, task_id: str) -> str:
        """
        Subscribes to a task and notifies when it's done.
        This is a non-blocking way to subscribe to the completion of a task.

        Args:
            task_id: ID of the task to subscribe to

        Returns:
            str: Command output from waiting for the task
        """
        # Start waiting for the task asynchronously
        result = await self.wait_for_task(task_id)
        self.logger.info(f"Task {task_id} finished:\n{result}")
        return result

    async def submit_and_wait(self, command: str, label: Optional[str] = None) -> str:
        """
        Submit a new task and subscribe to it for completion notification.

        Args:
            command: The command to execute
            label: Optional label for the task

        Returns:
            Task ID as string
        """
        # Add a task asynchronously
        task_id = await self.add_task(command, label)
        self.logger.info(f"Task {task_id} added, now waiting for it to complete.")

        # Subscribe to the task for completion
        await self.subscribe_to_task(task_id)

        return task_id

    async def submit_and_wait_and_get_output(
        self, command: str, label: Optional[str] = None
    ) -> str:
        """
        Submit a new task, wait for completion, and return the task output.

        Args:
            command: The command to execute
            label: Optional label for the task

        Returns:
            str: The stdout output from the task
        """
        # Add a task asynchronously
        task_id = await self.add_task(command, label)
        self.logger.info(f"Task {task_id} added, now waiting for it to complete.")

        # Subscribe to the task for completion
        await self.subscribe_to_task(task_id)

        # Get the output of the task
        response = await self.get_logs_json([int(task_id)])
        task_stdout = response.get(task_id).output

        return task_stdout


class SyncAdvancedMixin:
    """
    Synchronous version of AdvancedMixin for use with sync wrappers.
    """

    def subscribe_to_task(self, task_id: str) -> str:
        """
        Subscribes to a task and notifies when it's done synchronously.

        Args:
            task_id: ID of the task to subscribe to

        Returns:
            str: Command output from waiting for the task
        """
        return self._run_async_method("subscribe_to_task", task_id)

    def submit_and_wait(self, command: str, label: Optional[str] = None) -> str:
        """
        Submit a new task and subscribe to it for completion notification synchronously.

        Args:
            command: The command to execute
            label: Optional label for the task

        Returns:
            Task ID as string
        """
        return self._run_async_method("submit_and_wait", command, label)

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
