import asyncio
import subprocess
import json
from loguru import logger
from typing import Dict, List, Optional, Union
from pueue_wrapper.models.logs import PueueLogResponse, TaskLogEntry
from pueue_wrapper.models.status import PueueStatus, Group
from pueue_wrapper.models.base import TaskControl


class PueueAsyncCore:
    """
    Core async implementation for Pueue CLI interaction.

    This class provides the fundamental operations for interacting with the Pueue daemon,
    including basic task management, status queries, group management, and logging operations.
    """

    def __init__(self):
        self.processes = {}
        self.logger = logger.bind(module="pueue_async_core")

    async def _run_pueue_command(self, *args) -> str:
        """
        Runs a pueue command asynchronously and returns the process output.

        Args:
            *args: Command arguments to pass to pueue

        Returns:
            str: Command output from stdout

        Raises:
            Exception: If the command fails (non-zero return code)
        """
        proc = await asyncio.create_subprocess_exec(
            "pueue", *args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise Exception(f"Pueue command failed: {stderr.decode()}")
        return stdout.decode()

    # Basic Task Operations

    async def add_task(
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
        Adds a task to the Pueue queue asynchronously and returns the task ID.

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
        args = ["add"]

        # Always print task ID for programmatic use
        if print_task_id:
            args.append("--print-task-id")

        # Add optional parameters
        if working_directory:
            args.extend(["--working-directory", working_directory])
        if group:
            args.extend(["--group", group])
        if priority is not None:
            args.extend(["--priority", str(priority)])
        if after:
            for dep_id in after:
                args.extend(["--after", str(dep_id)])
        if delay:
            args.extend(["--delay", delay])
        if label:
            args.extend(["--label", label])
        if immediate:
            args.append("--immediate")
        if follow:
            args.append("--follow")
        if stashed:
            args.append("--stashed")
        if escape:
            args.append("--escape")

        args.append(command)
        task_id_output = await self._run_pueue_command(*args)
        return task_id_output.strip()

    async def wait_for_task(self, task_id: str) -> str:
        """
        Wait for a specific task to finish without blocking other tasks.

        Args:
            task_id: ID of the task to wait for

        Returns:
            str: Command output
        """
        return await self._run_pueue_command("wait", task_id)

    async def remove_task(self, task_ids: Union[int, List[int]]) -> TaskControl:
        """
        Remove tasks from the queue.

        Args:
            task_ids: Single task ID or list of task IDs to remove

        Returns:
            TaskControl object indicating success/failure
        """
        try:
            if isinstance(task_ids, int):
                task_ids = [task_ids]
            args = ["remove"] + [str(tid) for tid in task_ids]
            await self._run_pueue_command(*args)
            return TaskControl(
                success=True, message=f"Removed tasks: {task_ids}", task_ids=task_ids
            )
        except Exception as e:
            return TaskControl(success=False, message=str(e))

    async def kill_task(
        self, task_ids: Union[int, List[int]], group: Optional[str] = None
    ) -> TaskControl:
        """
        Kill running tasks.

        Args:
            task_ids: Single task ID or list of task IDs to kill
            group: Optional group to kill all tasks in

        Returns:
            TaskControl object indicating success/failure
        """
        try:
            args = ["kill"]
            if group:
                args.extend(["--group", group])
            else:
                if isinstance(task_ids, int):
                    task_ids = [task_ids]
                args.extend([str(tid) for tid in task_ids])
            await self._run_pueue_command(*args)
            return TaskControl(
                success=True,
                message=(
                    f"Killed tasks: {task_ids}"
                    if not group
                    else f"Killed all tasks in group '{group}'"
                ),
                task_ids=task_ids if not group else None,
            )
        except Exception as e:
            return TaskControl(success=False, message=str(e))

    async def pause_task(
        self, task_ids: Union[int, List[int]], group: Optional[str] = None
    ) -> TaskControl:
        """
        Pause tasks or groups.

        Args:
            task_ids: Single task ID or list of task IDs to pause
            group: Optional group to pause all tasks in

        Returns:
            TaskControl object indicating success/failure
        """
        try:
            args = ["pause"]
            if group:
                args.extend(["--group", group])
            else:
                if isinstance(task_ids, int):
                    task_ids = [task_ids]
                args.extend([str(tid) for tid in task_ids])
            await self._run_pueue_command(*args)
            return TaskControl(
                success=True,
                message=(
                    f"Paused tasks: {task_ids}"
                    if not group
                    else f"Paused group '{group}'"
                ),
                task_ids=task_ids if not group else None,
            )
        except Exception as e:
            return TaskControl(success=False, message=str(e))

    async def start_task(
        self, task_ids: Union[int, List[int]], group: Optional[str] = None
    ) -> TaskControl:
        """
        Start/resume tasks or groups.

        Args:
            task_ids: Single task ID or list of task IDs to start
            group: Optional group to start all tasks in

        Returns:
            TaskControl object indicating success/failure
        """
        try:
            args = ["start"]
            if group:
                args.extend(["--group", group])
            else:
                if isinstance(task_ids, int):
                    task_ids = [task_ids]
                args.extend([str(tid) for tid in task_ids])
            await self._run_pueue_command(*args)
            return TaskControl(
                success=True,
                message=(
                    f"Started tasks: {task_ids}"
                    if not group
                    else f"Started group '{group}'"
                ),
                task_ids=task_ids if not group else None,
            )
        except Exception as e:
            return TaskControl(success=False, message=str(e))

    async def restart_task(
        self, task_ids: Union[int, List[int]], in_place: bool = False
    ) -> TaskControl:
        """
        Restart tasks.

        Args:
            task_ids: Single task ID or list of task IDs to restart
            in_place: Restart in place (keep same task ID)

        Returns:
            TaskControl object indicating success/failure
        """
        try:
            if isinstance(task_ids, int):
                task_ids = [task_ids]
            args = ["restart"]
            if in_place:
                args.append("--in-place")
            args.extend([str(tid) for tid in task_ids])
            await self._run_pueue_command(*args)
            return TaskControl(
                success=True, message=f"Restarted tasks: {task_ids}", task_ids=task_ids
            )
        except Exception as e:
            return TaskControl(success=False, message=str(e))

    async def clean_tasks(self, group: Optional[str] = None) -> TaskControl:
        """
        Clean finished tasks from the list.

        Args:
            group: Optional group to clean (cleans all groups if not specified)

        Returns:
            TaskControl object indicating success/failure
        """
        try:
            args = ["clean"]
            if group:
                args.extend(["--group", group])
            await self._run_pueue_command(*args)
            message = (
                f"Cleaned tasks in group '{group}'"
                if group
                else "Cleaned all finished tasks"
            )
            return TaskControl(success=True, message=message)
        except Exception as e:
            return TaskControl(success=False, message=str(e))

    async def reset_queue(
        self, groups: Optional[List[str]] = None, force: bool = False
    ) -> TaskControl:
        """
        Reset the queue (remove all tasks).

        Args:
            groups: Optional list of group names to reset (resets all groups if not specified)
            force: Don't ask for confirmation

        Returns:
            TaskControl object indicating success/failure
        """
        try:
            args = ["reset"]
            if force:
                args.append("--force")
            if groups:
                args.extend(["--groups", ",".join(groups)])
            await self._run_pueue_command(*args)
            message = (
                f"Reset queue for groups: {groups}" if groups else "Reset entire queue"
            )
            return TaskControl(success=True, message=message)
        except Exception as e:
            return TaskControl(success=False, message=str(e))

    # Status and Query Operations

    async def get_status(self, group: Optional[str] = None) -> PueueStatus:
        """
        Retrieves the status of all tasks or tasks from a specific group.

        Args:
            group: Optional group name to filter tasks by

        Returns:
            PueueStatus: The status data for tasks
        """
        args = ["status", "--json"]
        if group:
            args.extend(["--group", group])

        status_output = await self._run_pueue_command(*args)
        status_data = json.loads(status_output)
        return PueueStatus.model_validate(status_data)

    async def get_log(
        self, task_ids: Union[int, List[int]], group: Optional[str] = None
    ) -> str:
        """
        Retrieves the log of specific tasks in text format.

        Args:
            task_ids: Single task ID or list of task IDs to retrieve
            group: Optional group to filter tasks by

        Returns:
            str: The log output for the specified tasks
        """
        args = ["log"]

        # Add group filter if specified
        if group:
            args.extend(["--group", group])

        # Add task IDs
        if isinstance(task_ids, int):
            args.append(str(task_ids))
        else:
            args.extend([str(tid) for tid in task_ids])

        return await self._run_pueue_command(*args)

    async def get_logs_json(
        self,
        task_ids: Optional[Union[int, List[int]]] = None,
        group: Optional[str] = None,
    ) -> PueueLogResponse:
        """
        Retrieves the logs of all tasks or specific tasks in JSON format.

        Args:
            task_ids: Optional single task ID or list of task IDs to retrieve. If None, gets all tasks.
            group: Optional group to filter tasks by

        Returns:
            PueueLogResponse: Structured log data for all requested tasks
        """
        args = ["log", "--json"]

        # Add group filter if specified
        if group:
            args.extend(["--group", group])

        # Add task IDs if specified
        if task_ids is not None:
            if isinstance(task_ids, int):
                args.append(str(task_ids))
            else:
                args.extend([str(tid) for tid in task_ids])

        log_output = await self._run_pueue_command(*args)
        log_data = json.loads(log_output)

        # If specific task_ids were requested, filter the response
        if task_ids is not None:
            task_id_strs = (
                [str(task_ids)]
                if isinstance(task_ids, int)
                else [str(tid) for tid in task_ids]
            )
            filtered_data = {
                task_id: log_data[task_id]
                for task_id in task_id_strs
                if task_id in log_data
            }
            log_data = filtered_data

        return PueueLogResponse.model_validate(log_data)

    async def get_task_log_entry(
        self, task_id: Union[int, str]
    ) -> Optional[TaskLogEntry]:
        """
        Retrieves a single task's log entry with structured data.

        Args:
            task_id: The ID of the task to retrieve

        Returns:
            TaskLogEntry: The structured log entry for the task, or None if not found
        """
        task_id_int = int(task_id)
        logs = await self.get_logs_json(task_id_int)
        return logs.get(str(task_id_int))

    # Group Management Operations

    async def get_groups(self) -> Dict[str, Group]:
        """
        Get all groups and their status.

        Returns:
            Dict mapping group names to Group objects
        """
        output = await self._run_pueue_command("group", "-j")
        groups_data = json.loads(output)
        return {name: Group.model_validate(data) for name, data in groups_data.items()}

    async def add_group(self, group_name: str) -> TaskControl:
        """
        Add a new group.

        Args:
            group_name: Name of the group to create

        Returns:
            TaskControl object indicating success/failure
        """
        try:
            await self._run_pueue_command("group", "add", group_name)
            return TaskControl(
                success=True, message=f"Group '{group_name}' created successfully"
            )
        except Exception as e:
            return TaskControl(success=False, message=str(e))

    async def remove_group(
        self, group_name: str, force_clean: bool = True
    ) -> TaskControl:
        """
        Remove a group. Optionally cleans all tasks in the group first.

        Args:
            group_name: Name of the group to remove
            force_clean: If True, clean all tasks in the group before removing it

        Returns:
            TaskControl object indicating success/failure
        """
        try:
            if force_clean:
                # First, clean all tasks in the group
                clean_result = await self.clean_tasks(group_name)
                if not clean_result.success:
                    return TaskControl(
                        success=False,
                        message=f"Failed to clean tasks in group '{group_name}': {clean_result.message}",
                    )

            # Now try to remove the group
            await self._run_pueue_command("group", "remove", group_name)

            message = f"Group '{group_name}' removed successfully"
            if force_clean:
                message += " (tasks were cleaned first)"

            return TaskControl(success=True, message=message)
        except Exception as e:
            return TaskControl(success=False, message=str(e))

    async def set_group_parallel(
        self, parallel_tasks: int, group: Optional[str] = None
    ) -> TaskControl:
        """
        Set the number of parallel tasks for a group.

        Args:
            parallel_tasks: Number of parallel tasks to allow
            group: Group name (defaults to 'default' if not specified)

        Returns:
            TaskControl object indicating success/failure
        """
        try:
            args = ["parallel", str(parallel_tasks)]
            if group:
                args.extend(["--group", group])
            await self._run_pueue_command(*args)
            group_name = group or "default"
            return TaskControl(
                success=True,
                message=f"Set parallel tasks to {parallel_tasks} for group '{group_name}'",
            )
        except Exception as e:
            return TaskControl(success=False, message=str(e))
