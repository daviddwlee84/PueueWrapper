import asyncio
from loguru import logger
from .core.async_core import PueueAsyncCore
from .extensions.statistics import StatisticsMixin
from .extensions.advanced import AdvancedMixin


class PueueWrapper(PueueAsyncCore, StatisticsMixin, AdvancedMixin):
    """
    Complete async wrapper for Pueue with all functionality.

    This class combines the core Pueue CLI functionality with statistical analysis
    and advanced convenience methods through multiple inheritance.
    """

    def __init__(self):
        super().__init__()
        self.logger = logger.bind(module="pueue_wrapper")


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

        # Demo statistics functionality
        logger.info("=== Testing statistics functionality ===")

        # Get group statistics
        group_stats = await pueue.get_group_statistics("default")
        logger.info(f"Group 'default' statistics:")
        logger.info(f"  Total tasks: {group_stats.total_tasks}")
        logger.info(f"  Completed: {group_stats.completed_tasks}")
        logger.info(f"  Failed: {group_stats.failed_tasks}")
        logger.info(f"  Success rate: {group_stats.success_rate:.2%}")

        # Get time statistics if there are completed tasks
        if group_stats.completed_tasks > 0:
            time_stats = await pueue.get_group_time_statistics("default")
            logger.info(f"Time statistics:")
            logger.info(f"  Average duration: {time_stats.avg_duration:.2f}s")
            logger.info(f"  Tasks per hour: {time_stats.tasks_per_hour:.2f}")


if __name__ == "__main__":
    asyncio.run(main())
