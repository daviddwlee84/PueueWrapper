import asyncio
import subprocess
from loguru import logger
import json
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from pydantic import BaseModel, Field, RootModel
from pueue_wrapper.models.logs import PueueLogResponse, TaskLogEntry, LogTask
from pueue_wrapper.models.status import PueueStatus, Task, Group
from pueue_wrapper.models.base import TaskStatusInfo, TaskAddOptions, TaskControl


class PueueWrapper:
    def __init__(self):
        self.processes = {}
        self.logger = logger.bind(module="pueue_wrapper")

    async def _run_pueue_command(self, *args) -> str:
        """
        Runs a pueue command asynchronously and returns the process output.
        """
        proc = await asyncio.create_subprocess_exec(
            "pueue", *args, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise Exception(f"Pueue command failed: {stderr.decode()}")
        return stdout.decode()

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
        return task_id_output.strip()  # Get only the task ID from the output

    async def wait_for_task(self, task_id: str) -> str:
        """
        Wait for a specific task to finish without blocking other tasks.
        """
        # Running pueue wait in the background
        return await self._run_pueue_command("wait", task_id)

    async def subscribe_to_task(self, task_id: str) -> str:
        """
        Subscribes to a task and notifies when it's done.
        This is a non-blocking way to subscribe to the completion of a task.
        """
        # Start waiting for the task asynchronously
        result = await self.wait_for_task(task_id)
        self.logger.info(f"Task {task_id} finished:\n{result}")

    async def submit_and_wait(self, command: str, label: Optional[str] = None) -> str:
        """
        Submit a new task and subscribe to it for completion notification.
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
        response = await self.get_logs_json([task_id])
        task_stdout = response.get(task_id).output

        return task_stdout

    async def get_status(self) -> PueueStatus:
        """
        Retrieves the status of all tasks.
        """
        # Get status in JSON format
        status_output = await self._run_pueue_command("status", "--json")
        status_data = json.loads(status_output)
        return PueueStatus.model_validate(status_data)

    async def get_log(self, task_id: str) -> str:
        """
        Retrieves the log of a specific task in text format.
        """
        return await self._run_pueue_command("log", task_id)

    async def get_logs_json(
        self, task_ids: Optional[List[str]] = None
    ) -> PueueLogResponse:
        """
        Retrieves the logs of all tasks or specific tasks in JSON format.

        Args:
            task_ids: Optional list of task IDs to retrieve. If None, gets all tasks.

        Returns:
            PueueLogResponse: Structured log data for all requested tasks
        """
        # Get logs in JSON format - pueue log -j gets all task logs
        if task_ids:
            # For specific task IDs, we'll need to filter the response
            log_output = await self._run_pueue_command("log", "--json")
        else:
            log_output = await self._run_pueue_command("log", "--json")

        log_data = json.loads(log_output)

        # Filter by task_ids if provided
        if task_ids:
            filtered_data = {
                task_id: log_data[task_id]
                for task_id in task_ids
                if task_id in log_data
            }
            log_data = filtered_data

        return PueueLogResponse.model_validate(log_data)

    async def get_task_log_entry(self, task_id: str) -> Optional[TaskLogEntry]:
        """
        Retrieves a single task's log entry with structured data.

        Args:
            task_id: The ID of the task to retrieve

        Returns:
            TaskLogEntry: The structured log entry for the task, or None if not found
        """
        logs = await self.get_logs_json([task_id])
        return logs.get(task_id)

    # Group Management Methods

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

    async def remove_group(self, group_name: str) -> TaskControl:
        """
        Remove a group.

        Args:
            group_name: Name of the group to remove

        Returns:
            TaskControl object indicating success/failure
        """
        try:
            await self._run_pueue_command("group", "remove", group_name)
            return TaskControl(
                success=True, message=f"Group '{group_name}' removed successfully"
            )
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

    # Task Control Methods

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

    async def reset_queue(self, group: Optional[str] = None) -> TaskControl:
        """
        Reset the queue (remove all tasks).

        Args:
            group: Optional group to reset (resets all groups if not specified)

        Returns:
            TaskControl object indicating success/failure
        """
        try:
            args = ["reset"]
            if group:
                args.extend(["--group", group])
            await self._run_pueue_command(*args)
            message = (
                f"Reset queue for group '{group}'" if group else "Reset entire queue"
            )
            return TaskControl(success=True, message=message)
        except Exception as e:
            return TaskControl(success=False, message=str(e))


# Example of usage
async def main():
    pueue = PueueWrapper()

    # Submit a task and wait for it asynchronously
    task_id = await pueue.submit_and_wait('echo "Hello, Pueue!"')
    logger.info(await pueue.get_log(task_id))

    # You can submit and monitor multiple tasks concurrently
    await asyncio.gather(
        pueue.submit_and_wait("sleep 3", "Sleep 3 seconds"),
        pueue.submit_and_wait("sleep 5"),
    )

    # Get structured status
    status = await pueue.get_status()
    task_ids = list(status.tasks.keys())
    logger.info(f"Tasks: {task_ids}")
    logger.info(f"Default group status: {status.groups['default'].status}")

    # Log details about first task if any exist
    if task_ids:
        first_task = status.tasks[task_ids[0]]
        logger.info(f"First task command: {first_task.command}")
        # Get the status type (e.g., "Done", "Running") and its info
        status_type = next(iter(first_task.status))
        status_info = first_task.status[status_type]
        logger.info(f"First task status: {status_type}, result: {status_info.result}")

        # Demo new structured log functionality
        logger.info("=== Testing new structured log functionality ===")

        # Get single task log entry
        task_log_entry = await pueue.get_task_log_entry(task_ids[0])
        if task_log_entry:
            logger.info(
                f"Task {task_log_entry.task.id} output: {task_log_entry.output}"
            )
            logger.info(f"Task command: {task_log_entry.task.command}")
            logger.info(f"Task created at: {task_log_entry.task.created_at}")
            logger.info(f"Task path: {task_log_entry.task.path}")

        # Get all logs in structured format
        all_logs = await pueue.get_logs_json()
        logger.info(f"Total tasks in logs: {len(all_logs)}")

        # Demo iteration over log response
        for task_id, log_entry in all_logs.items():
            task = log_entry.task
            logger.info(
                f"Task {task_id}: {task.original_command} -> {log_entry.output[:50]}..."
            )

        # Get logs for specific tasks only
        if len(task_ids) >= 2:
            specific_logs = await pueue.get_logs_json(task_ids[:2])
            logger.info(
                f"Specific logs for first 2 tasks: {list(specific_logs.keys())}"
            )


if __name__ == "__main__":
    asyncio.run(main())
