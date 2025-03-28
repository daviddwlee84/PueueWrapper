import asyncio
import subprocess
from loguru import logger


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

    async def add_task(self, command: str) -> str:
        """
        Adds a task to the Pueue queue asynchronously and returns the task ID.
        """
        task_id_output = await self._run_pueue_command(
            "add", "--print-task-id", command
        )
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

    async def submit_and_wait(self, command: str) -> str:
        """
        Submit a new task and subscribe to it for completion notification.
        """
        # Add a task asynchronously
        task_id = await self.add_task(command)
        self.logger.info(f"Task {task_id} added, now waiting for it to complete.")

        # Subscribe to the task for completion
        await self.subscribe_to_task(task_id)

        return task_id

    async def get_status(self) -> str:
        """
        Retrieves the status of all tasks.
        """
        # TODO: we should get JSON format
        return await self._run_pueue_command("status")

    async def get_log(self, task_id: str) -> str:
        """
        Retrieves the log of a specific task.
        """
        # TODO: we should get JSON format
        return await self._run_pueue_command("log", task_id)


# Example of usage
async def main():
    pueue = PueueWrapper()

    # Submit a task and wait for it asynchronously
    task_id = await pueue.submit_and_wait('echo "Hello, Pueue!"')
    logger.info(await pueue.get_log(task_id))

    # You can submit and monitor multiple tasks concurrently
    await asyncio.gather(
        pueue.submit_and_wait("sleep 3"),
        pueue.submit_and_wait("sleep 5"),
    )

    logger.info(await pueue.get_status())


if __name__ == "__main__":
    asyncio.run(main())
