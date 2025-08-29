from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, RedirectResponse
from pueue_wrapper import PueueWrapper
from pueue_wrapper.models.status import PueueStatus, Group
from pueue_wrapper.models.logs import PueueLogResponse, TaskLogEntry
from pueue_wrapper.models.base import TaskControl
from typing import Optional, List, Dict, Union

# FastAPI setup
app = FastAPI()

# PueueWrapper instance
pueue = PueueWrapper()


@app.get("/api/add")
async def add_task(
    command: str,
    label: Optional[str] = None,
    working_directory: Optional[str] = None,
    group: Optional[str] = None,
    priority: Optional[int] = None,
    after: Optional[str] = None,  # Comma-separated task IDs
    delay: Optional[str] = None,
    immediate: bool = False,
    follow: bool = False,
    stashed: bool = False,
    escape: bool = False,
    print_task_id: bool = True,
) -> str:
    """
    Add a task to Pueue asynchronously with full options support.

    Args:
        command: The command to execute
        label: Optional label for the task
        working_directory: Working directory for the task
        group: Group to assign the task to
        priority: Priority level (higher number = higher priority)
        after: Comma-separated list of task IDs this task depends on (e.g., "1,2,3")
        delay: Delay before enqueueing (e.g., "10s", "5m", "1h")
        immediate: Start the task immediately
        follow: Follow the task output if started immediately
        stashed: Create task in stashed state
        escape: Escape special shell characters
        print_task_id: Return only task ID (True by default)

    Returns:
        Task ID as string
    """
    try:
        # Parse after parameter
        after_list = None
        if after:
            after_list = [int(tid.strip()) for tid in after.split(",")]

        task_id = await pueue.add_task(
            command=command,
            label=label,
            working_directory=working_directory,
            group=group,
            priority=priority,
            after=after_list,
            delay=delay,
            immediate=immediate,
            follow=follow,
            stashed=stashed,
            escape=escape,
            print_task_id=print_task_id,
        )
        return task_id
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/wait/{task_id}")
async def wait_for_task(task_id: str) -> str:
    """
    Wait for a specific task to finish asynchronously.
    """
    try:
        result = await pueue.wait_for_task(task_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/subscribe/{task_id}")
async def subscribe_to_task(task_id: str):
    """
    Subscribe to a task and notify when it finishes using Server-Sent Events (SSE).
    """

    async def event_stream():
        try:
            result = await pueue.subscribe_to_task(task_id)
            yield f"data: {result}\n\n"
        except Exception as e:
            yield f"data: Task failed: {str(e)}\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/api/submit_and_wait")
async def submit_and_wait(command: str, label: Optional[str] = None) -> str:
    """
    Submit a task and wait for it asynchronously.
    """
    try:
        result = await pueue.submit_and_wait(command, label)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/submit_and_wait_and_get_output")
async def submit_and_wait_and_get_output(
    command: str, label: Optional[str] = None
) -> str:
    """
    Submit a task, wait for completion, and return the task output.

    Args:
        command: The command to execute
        label: Optional label for the task

    Returns:
        str: The stdout output from the task
    """
    try:
        result = await pueue.submit_and_wait_and_get_output(command, label)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/status")
async def get_status() -> PueueStatus:
    """
    List the status of all tasks.
    Returns a structured PueueStatus object with tasks and groups information.
    """
    try:
        status = await pueue.get_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/log/{task_id}")
async def get_log(task_id: str) -> str:
    """
    Retrieve the log of a specific task in text format.
    """
    try:
        log = await pueue.get_log(task_id)
        return log
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/logs/json")
async def get_logs_json(task_ids: Optional[str] = None) -> PueueLogResponse:
    """
    Retrieve structured logs for all tasks or specific tasks.

    Args:
        task_ids: Optional comma-separated list of task IDs (e.g., "1,2,3")
    """
    try:
        task_id_list = None
        if task_ids:
            task_id_list = [tid.strip() for tid in task_ids.split(",")]
        logs = await pueue.get_logs_json(task_id_list)
        return logs
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/log/{task_id}/json")
async def get_task_log_entry(task_id: str) -> TaskLogEntry:
    """
    Retrieve structured log entry for a specific task.
    """
    try:
        log_entry = await pueue.get_task_log_entry(task_id)
        if log_entry is None:
            raise HTTPException(status_code=404, detail=f"Task {task_id} not found")
        return log_entry
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Group Management Endpoints


@app.get("/api/groups")
async def get_groups() -> Dict[str, Group]:
    """
    Get all groups and their status.
    """
    try:
        groups = await pueue.get_groups()
        return groups
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/groups/{group_name}")
async def add_group(group_name: str) -> TaskControl:
    """
    Add a new group.
    """
    try:
        result = await pueue.add_group(group_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/groups/{group_name}")
async def remove_group(group_name: str) -> TaskControl:
    """
    Remove a group.
    """
    try:
        result = await pueue.remove_group(group_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/api/groups/{group_name}/parallel")
async def set_group_parallel(
    group_name: Optional[str] = None, parallel_tasks: int = 1
) -> TaskControl:
    """
    Set the number of parallel tasks for a group.
    """
    try:
        result = await pueue.set_group_parallel(parallel_tasks, group_name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Task Control Endpoints


@app.delete("/api/tasks")
async def remove_task(task_ids: str) -> TaskControl:
    """
    Remove tasks from the queue.

    Args:
        task_ids: Comma-separated list of task IDs (e.g., "1,2,3")
    """
    try:
        task_id_list = [int(tid.strip()) for tid in task_ids.split(",")]
        result = await pueue.remove_task(task_id_list)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tasks/kill")
async def kill_task(
    task_ids: Optional[str] = None, group: Optional[str] = None
) -> TaskControl:
    """
    Kill running tasks.

    Args:
        task_ids: Comma-separated list of task IDs (e.g., "1,2,3")
        group: Optional group to kill all tasks in
    """
    try:
        if task_ids:
            task_id_list = [int(tid.strip()) for tid in task_ids.split(",")]
            result = await pueue.kill_task(task_id_list, group)
        elif group:
            result = await pueue.kill_task([], group)
        else:
            raise HTTPException(
                status_code=400, detail="Either task_ids or group must be specified"
            )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tasks/pause")
async def pause_task(
    task_ids: Optional[str] = None, group: Optional[str] = None
) -> TaskControl:
    """
    Pause tasks or groups.

    Args:
        task_ids: Comma-separated list of task IDs (e.g., "1,2,3")
        group: Optional group to pause all tasks in
    """
    try:
        if task_ids:
            task_id_list = [int(tid.strip()) for tid in task_ids.split(",")]
            result = await pueue.pause_task(task_id_list, group)
        elif group:
            result = await pueue.pause_task([], group)
        else:
            raise HTTPException(
                status_code=400, detail="Either task_ids or group must be specified"
            )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tasks/start")
async def start_task(
    task_ids: Optional[str] = None, group: Optional[str] = None
) -> TaskControl:
    """
    Start/resume tasks or groups.

    Args:
        task_ids: Comma-separated list of task IDs (e.g., "1,2,3")
        group: Optional group to start all tasks in
    """
    try:
        if task_ids:
            task_id_list = [int(tid.strip()) for tid in task_ids.split(",")]
            result = await pueue.start_task(task_id_list, group)
        elif group:
            result = await pueue.start_task([], group)
        else:
            raise HTTPException(
                status_code=400, detail="Either task_ids or group must be specified"
            )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/tasks/restart")
async def restart_task(task_ids: str, in_place: bool = False) -> TaskControl:
    """
    Restart tasks.

    Args:
        task_ids: Comma-separated list of task IDs (e.g., "1,2,3")
        in_place: Restart in place (keep same task ID)
    """
    try:
        task_id_list = [int(tid.strip()) for tid in task_ids.split(",")]
        result = await pueue.restart_task(task_id_list, in_place)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/tasks/clean")
async def clean_tasks(group: Optional[str] = None) -> TaskControl:
    """
    Clean finished tasks from the list.

    Args:
        group: Optional group to clean (cleans all groups if not specified)
    """
    try:
        result = await pueue.clean_tasks(group)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/api/tasks/reset")
async def reset_queue(groups: Optional[str] = None, force: bool = False) -> TaskControl:
    """
    Reset the queue (remove all tasks).

    Args:
        groups: Optional comma-separated list of group names to reset (resets all groups if not specified)
        force: Don't ask for confirmation
    """
    try:
        groups_list = None
        if groups:
            groups_list = [g.strip() for g in groups.split(",")]
        result = await pueue.reset_queue(groups_list, force)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")


if __name__ == "__main__":
    # python -m uvicorn api:app --reload
    # https://127.0.0.1:8000/docs
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
