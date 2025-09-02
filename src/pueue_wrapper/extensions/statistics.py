import statistics
from datetime import timedelta
from typing import Dict, List, Any
from pueue_wrapper.models.base import GroupStatistics, GroupTimeStatistics


class StatisticsMixin:
    """
    Mixin class providing statistical analysis functionality for Pueue tasks and groups.

    This mixin adds methods for analyzing task performance, completion rates,
    and time-based statistics for groups and tasks.
    """

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
        """
        Create duration buckets for histogram visualization.

        Args:
            durations: List of task durations in seconds

        Returns:
            Dict mapping bucket labels to counts
        """
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


class SyncStatisticsMixin:
    """
    Synchronous version of StatisticsMixin for use with sync wrappers.
    """

    def get_group_statistics(self, group_name: str) -> GroupStatistics:
        """
        Get statistics for a specific group synchronously.

        Args:
            group_name: Name of the group to get statistics for

        Returns:
            GroupStatistics: Statistics for the group including completion rates
        """
        return self._run_async_method("get_group_statistics", group_name)

    def get_group_time_statistics(self, group_name: str) -> GroupTimeStatistics:
        """
        Get detailed time-based statistics for a group synchronously.

        Args:
            group_name: Name of the group to analyze

        Returns:
            GroupTimeStatistics: Detailed time statistics
        """
        return self._run_async_method("get_group_time_statistics", group_name)
