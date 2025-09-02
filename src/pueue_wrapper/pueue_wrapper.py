import asyncio
import subprocess
from loguru import logger
import json
from typing import Dict, List, Optional, Union, Any
from datetime import datetime
from pydantic import BaseModel, Field, RootModel
from pueue_wrapper.models.logs import PueueLogResponse, TaskLogEntry, LogTask
from pueue_wrapper.models.status import PueueStatus, Task, Group
from pueue_wrapper.models.base import (
    TaskStatusInfo,
    TaskAddOptions,
    TaskControl,
    GroupStatistics,
    GroupTimeStatistics,
)


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
        response = await self.get_logs_json([int(task_id)])
        task_stdout = response.get(task_id).output

        return task_stdout

    async def get_status(self, group: Optional[str] = None) -> PueueStatus:
        """
        Retrieves the status of all tasks or tasks from a specific group.

        Args:
            group: Optional group name to filter tasks by

        Returns:
            PueueStatus: The status data for tasks
        """
        # Get status in JSON format
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

    async def get_group_statistics(self, group_name: str) -> GroupStatistics:
        """
        Get statistics for a specific group.

        Args:
            group_name: Name of the group to get statistics for

        Returns:
            GroupStatistics: Statistics for the group including completion rates
        """
        # Get status data for the specific group
        status = await self.get_status(group=group_name)

        stats = GroupStatistics(group_name=group_name)

        # Count tasks by status
        for task in status.tasks.values():
            stats.total_tasks += 1

            # Get the status key (e.g., "Running", "Done", "Queued", etc.)
            status_key = list(task.status.keys())[0]

            # TODO: use match case
            if status_key == "Running":
                stats.running_tasks += 1
            elif status_key == "Queued":
                stats.queued_tasks += 1
            elif status_key == "Paused":
                stats.paused_tasks += 1
            elif status_key == "Stashed":
                stats.stashed_tasks += 1
            elif status_key == "Done":
                # Check if the task was successful or failed
                status_info = task.status[status_key]
                if hasattr(status_info, "result") and status_info.result is not None:
                    if self._is_task_successful(status_info.result):
                        stats.completed_tasks += 1
                    else:
                        stats.failed_tasks += 1
                else:
                    # If no result information, assume success
                    stats.completed_tasks += 1

        # Calculate rates
        stats.calculate_rates()

        return stats

    async def get_group_time_statistics(self, group_name: str) -> GroupTimeStatistics:
        """
        Get detailed time-based statistics for a group.

        Args:
            group_name: Name of the group to analyze

        Returns:
            GroupTimeStatistics: Detailed time statistics
        """
        import statistics
        from datetime import timedelta

        # Get group status first
        status = await self.get_status(group=group_name)
        if not status.tasks:
            return GroupTimeStatistics()

        time_stats = GroupTimeStatistics()

        # Collect task time data
        successful_durations = []
        failed_durations = []
        queue_times = []
        start_times = []
        end_times = []

        for task_id, task in status.tasks.items():
            if not task.status:
                continue

            status_key = list(task.status.keys())[0]
            status_info = task.status[status_key]

            # Extract time information
            start_time = getattr(status_info, "start", None)
            end_time = getattr(status_info, "end", None)
            enqueue_time = getattr(status_info, "enqueued_at", None)
            result = getattr(status_info, "result", None)

            # Record start and end times for overall time span
            if start_time:
                start_times.append(start_time)
            if end_time:
                end_times.append(end_time)

            # Calculate queue time (enqueue to start)
            if enqueue_time and start_time:
                queue_duration = (start_time - enqueue_time).total_seconds()
                if queue_duration >= 0:
                    queue_times.append(queue_duration)

            # Calculate task duration (start to end) for completed tasks
            if start_time and end_time and status_key == "Done":
                duration = (end_time - start_time).total_seconds()

                if self._is_task_successful(result):
                    successful_durations.append(duration)
                else:
                    failed_durations.append(duration)

        # Calculate time span statistics
        if start_times and end_times:
            time_stats.earliest_start_time = min(start_times)
            time_stats.latest_end_time = max(end_times)
            time_stats.total_time_span = (
                time_stats.latest_end_time - time_stats.earliest_start_time
            ).total_seconds()

        # Calculate duration statistics for successful tasks
        if successful_durations:
            time_stats.successful_tasks_count = len(successful_durations)
            time_stats.min_duration = min(successful_durations)
            time_stats.max_duration = max(successful_durations)
            time_stats.avg_duration = statistics.mean(successful_durations)
            time_stats.median_duration = statistics.median(successful_durations)

            if len(successful_durations) > 1:
                time_stats.std_duration = statistics.stdev(successful_durations)

            # Calculate percentiles
            sorted_durations = sorted(successful_durations)
            n = len(sorted_durations)
            time_stats.duration_percentiles = {
                "25%": sorted_durations[int(n * 0.25)] if n > 0 else 0,
                "50%": sorted_durations[int(n * 0.50)] if n > 0 else 0,
                "75%": sorted_durations[int(n * 0.75)] if n > 0 else 0,
                "95%": sorted_durations[int(n * 0.95)] if n > 0 else 0,
            }

            # Create duration buckets
            time_stats.duration_buckets = self._create_duration_buckets(
                successful_durations
            )

            # Calculate tasks per hour
            if time_stats.total_time_span and time_stats.total_time_span > 0:
                hours = time_stats.total_time_span / 3600
                time_stats.tasks_per_hour = len(successful_durations) / hours

        # Calculate average queue time
        if queue_times:
            time_stats.average_queue_time = statistics.mean(queue_times)

        # Calculate average duration for failed tasks
        if failed_durations:
            time_stats.failed_tasks_avg_duration = statistics.mean(failed_durations)

        return time_stats

    def _create_duration_buckets(self, durations: List[float]) -> Dict[str, int]:
        """Create duration buckets for histogram"""
        if not durations:
            return {}

        min_dur = min(durations)
        max_dur = max(durations)

        # Create 8 buckets
        bucket_size = (max_dur - min_dur) / 8 if max_dur > min_dur else 1
        buckets = {}

        for i in range(8):
            bucket_start = min_dur + i * bucket_size
            bucket_end = min_dur + (i + 1) * bucket_size

            if i == 7:  # Last bucket includes max value
                count = sum(1 for d in durations if bucket_start <= d <= bucket_end)
            else:
                count = sum(1 for d in durations if bucket_start <= d < bucket_end)

            # Format bucket label
            if bucket_size < 60:
                label = f"{bucket_start:.1f}s-{bucket_end:.1f}s"
            elif bucket_size < 3600:
                label = f"{bucket_start/60:.1f}m-{bucket_end/60:.1f}m"
            else:
                label = f"{bucket_start/3600:.1f}h-{bucket_end/3600:.1f}h"

            buckets[label] = count

        return buckets

    @staticmethod
    def _is_task_successful(result: Any) -> bool:
        """
        Check if a task result indicates success.
        # TODO: maybe this shouldn't be part of PueueWrapper (and we should make "result" a data model)

        Args:
            result: Task result which can be string or dict

        Returns:
            bool: True if task was successful, False otherwise
        """
        if result is None:
            return False  # No result typically means failed
        if isinstance(result, str):
            return result == "Success"
        if isinstance(result, dict):
            # Failed tasks typically have {"Failed": exit_code} format
            return "Failed" not in result
        return False  # Unknown format, assume failed

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
