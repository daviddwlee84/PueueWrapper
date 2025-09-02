import asyncio
import concurrent.futures
from typing import Dict, List, Optional, Union, Any
from .async_core import PueueAsyncCore
from pueue_wrapper.models.logs import PueueLogResponse, TaskLogEntry
from pueue_wrapper.models.status import PueueStatus, Group
from pueue_wrapper.models.base import TaskControl


class PueueSyncCore:
    """
    Core sync implementation for Pueue CLI interaction.

    This class provides synchronous wrappers around the core async functionality,
    allowing for easier integration in synchronous code.
    """

    def __init__(self):
        self.async_core = PueueAsyncCore()

    def _run_async_method(self, method: str, *args) -> Any:
        """
        A helper method to run async methods synchronously.
        Handles both cases where an event loop is already running and when it's not.

        Args:
            method: Name of the async method to call
            *args: Arguments to pass to the method

        Returns:
            Result from the async method
        """
        async_method = getattr(self.async_core, method)

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
        with concurrent.futures.ThreadPoolExecutor() as executor:
            future = executor.submit(run_in_thread)
            return future.result()

    # Basic Task Operations

    def add_task(
        self,
        command: str,
        label: Optional[str] = None,
        working_directory: Optional[str] = None,
        group: Optional[str] = None,
        priority: Optional[int] = None,
        after: Optional[List[int]] = None,
        delay: Optional[str] = None,
        immediate: bool = False,
        follow: bool = False,
        stashed: bool = False,
        escape: bool = False,
        print_task_id: bool = True,
    ) -> str:
        """
        Adds a task to the Pueue queue synchronously and returns the task ID.

        Args:
            command: The command to execute
            label: Optional label for the task
            working_directory: Working directory for the task
            group: Group to assign the task to
            priority: Priority level (higher number = higher priority)
            after: List of task IDs this task depends on
            delay: Delay before enqueueing (e.g., "10s", "5m", "1h")
            immediate: Start the task immediately
            follow: Follow the task output if started immediately
            stashed: Create task in stashed state
            escape: Escape special shell characters
            print_task_id: Return only task ID (True by default)

        Returns:
            Task ID as string
        """
        return self._run_async_method(
            "add_task",
            command,
            label,
            working_directory,
            group,
            priority,
            after,
            delay,
            immediate,
            follow,
            stashed,
            escape,
            print_task_id,
        )

    def wait_for_task(self, task_id: str) -> str:
        """
        Waits for a specific task to finish synchronously.

        Args:
            task_id: ID of the task to wait for

        Returns:
            str: Command output
        """
        return self._run_async_method("wait_for_task", task_id)

    def remove_task(self, task_ids: Union[int, List[int]]) -> TaskControl:
        """
        Remove tasks from the queue synchronously.

        Args:
            task_ids: Single task ID or list of task IDs to remove

        Returns:
            TaskControl object indicating success/failure
        """
        return self._run_async_method("remove_task", task_ids)

    def kill_task(
        self, task_ids: Union[int, List[int]], group: Optional[str] = None
    ) -> TaskControl:
        """
        Kill running tasks synchronously.

        Args:
            task_ids: Single task ID or list of task IDs to kill
            group: Optional group to kill all tasks in

        Returns:
            TaskControl object indicating success/failure
        """
        return self._run_async_method("kill_task", task_ids, group)

    def pause_task(
        self, task_ids: Union[int, List[int]], group: Optional[str] = None
    ) -> TaskControl:
        """
        Pause tasks or groups synchronously.

        Args:
            task_ids: Single task ID or list of task IDs to pause
            group: Optional group to pause all tasks in

        Returns:
            TaskControl object indicating success/failure
        """
        return self._run_async_method("pause_task", task_ids, group)

    def start_task(
        self, task_ids: Union[int, List[int]], group: Optional[str] = None
    ) -> TaskControl:
        """
        Start/resume tasks or groups synchronously.

        Args:
            task_ids: Single task ID or list of task IDs to start
            group: Optional group to start all tasks in

        Returns:
            TaskControl object indicating success/failure
        """
        return self._run_async_method("start_task", task_ids, group)

    def restart_task(
        self, task_ids: Union[int, List[int]], in_place: bool = False
    ) -> TaskControl:
        """
        Restart tasks synchronously.

        Args:
            task_ids: Single task ID or list of task IDs to restart
            in_place: Restart in place (keep same task ID)

        Returns:
            TaskControl object indicating success/failure
        """
        return self._run_async_method("restart_task", task_ids, in_place)

    def clean_tasks(self, group: Optional[str] = None) -> TaskControl:
        """
        Clean finished tasks from the list synchronously.

        Args:
            group: Optional group to clean (cleans all groups if not specified)

        Returns:
            TaskControl object indicating success/failure
        """
        return self._run_async_method("clean_tasks", group)

    def reset_queue(
        self, groups: Optional[List[str]] = None, force: bool = False
    ) -> TaskControl:
        """
        Reset the queue (remove all tasks) synchronously.

        Args:
            groups: Optional list of group names to reset (resets all groups if not specified)
            force: Don't ask for confirmation

        Returns:
            TaskControl object indicating success/failure
        """
        return self._run_async_method("reset_queue", groups, force)

    # Status and Query Operations

    def get_status(self, group: Optional[str] = None) -> PueueStatus:
        """
        Retrieves the status of all tasks or tasks from a specific group synchronously.

        Args:
            group: Optional group name to filter tasks by

        Returns:
            PueueStatus: The status data for tasks
        """
        return self._run_async_method("get_status", group)

    def get_log(
        self, task_ids: Union[int, List[int]], group: Optional[str] = None
    ) -> str:
        """
        Retrieves the log of specific tasks in text format synchronously.

        Args:
            task_ids: Single task ID or list of task IDs to retrieve
            group: Optional group to filter tasks by

        Returns:
            str: The log output for the specified tasks
        """
        return self._run_async_method("get_log", task_ids, group)

    def get_logs_json(
        self,
        task_ids: Optional[Union[int, List[int]]] = None,
        group: Optional[str] = None,
    ) -> PueueLogResponse:
        """
        Retrieves the logs of all tasks or specific tasks in JSON format synchronously.

        Args:
            task_ids: Optional single task ID or list of task IDs to retrieve. If None, gets all tasks.
            group: Optional group to filter tasks by

        Returns:
            PueueLogResponse: Structured log data for all requested tasks
        """
        return self._run_async_method("get_logs_json", task_ids, group)

    def get_task_log_entry(self, task_id: Union[int, str]) -> Optional[TaskLogEntry]:
        """
        Retrieves a single task's log entry with structured data synchronously.

        Args:
            task_id: The ID of the task to retrieve

        Returns:
            TaskLogEntry: The structured log entry for the task, or None if not found
        """
        return self._run_async_method("get_task_log_entry", task_id)

    # Group Management Operations

    def get_groups(self) -> Dict[str, Group]:
        """
        Get all groups and their status synchronously.

        Returns:
            Dict mapping group names to Group objects
        """
        return self._run_async_method("get_groups")

    def add_group(self, group_name: str) -> TaskControl:
        """
        Add a new group synchronously.

        Args:
            group_name: Name of the group to create

        Returns:
            TaskControl object indicating success/failure
        """
        return self._run_async_method("add_group", group_name)

    def remove_group(self, group_name: str, force_clean: bool = True) -> TaskControl:
        """
        Remove a group synchronously. Optionally cleans all tasks in the group first.

        Args:
            group_name: Name of the group to remove
            force_clean: If True, clean all tasks in the group before removing it

        Returns:
            TaskControl object indicating success/failure
        """
        return self._run_async_method("remove_group", group_name, force_clean)

    def set_group_parallel(
        self, parallel_tasks: int, group: Optional[str] = None
    ) -> TaskControl:
        """
        Set the number of parallel tasks for a group synchronously.

        Args:
            parallel_tasks: Number of parallel tasks to allow
            group: Group name (defaults to 'default' if not specified)

        Returns:
            TaskControl object indicating success/failure
        """
        return self._run_async_method("set_group_parallel", parallel_tasks, group)
