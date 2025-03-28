import asyncio
import subprocess

class PueueWrapper:
    def __init__(self):
        self.processes = {}

    async def _run_pueue_command(self, *args):
        """
        Runs a pueue command asynchronously and returns the process output.
        """
        proc = await asyncio.create_subprocess_exec(
            "pueue", *args,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise Exception(f"Pueue command failed: {stderr.decode()}")
        return stdout.decode()

    async def add_task(self, command):
        """
        Adds a task to the Pueue queue asynchronously and returns the task ID.
        """
        task_id_output = await self._run_pueue_command("add", "--print-task-id", command)
        return task_id_output.strip()  # Get only the task ID from the output

    async def wait_for_task(self, task_id):
        """
        Wait for a specific task to finish without blocking other tasks.
        """
        # Running pueue wait in the background
        return await self._run_pueue_command("wait", task_id)

    async def subscribe_to_task(self, task_id):
        """
        Subscribes to a task and notifies when it's done.
        This is a non-blocking way to subscribe to the completion of a task.
        """
        # Start waiting for the task asynchronously
        result = await self.wait_for_task(task_id)
        print(f"Task {task_id} finished:\n{result}")

    async def submit_and_wait(self, command):
        """
        Submit a new task and subscribe to it for completion notification.
        """
        # Add a task asynchronously
        task_id = await self.add_task(command)
        task_id = task_id.strip()  # Assuming the output is just the task ID
        print(f"Task {task_id} added, now waiting for it to complete.")
        
        # Subscribe to the task for completion
        await self.subscribe_to_task(task_id)

# Example of usage
async def main():
    pueue = PueueWrapper()

    # Submit a task and wait for it asynchronously
    await pueue.submit_and_wait('echo "Hello, Pueue!"')

    # You can submit and monitor multiple tasks concurrently
    await asyncio.gather(
        pueue.submit_and_wait('sleep 3'),
        pueue.submit_and_wait('sleep 5'),
    )

if __name__ == "__main__":
    asyncio.run(main())
