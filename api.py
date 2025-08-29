from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse, RedirectResponse
from pueue_wrapper import PueueWrapper
from models.status import PueueStatus
from models.logs import PueueLogResponse, TaskLogEntry
from typing import Optional, List

# FastAPI setup
app = FastAPI()

# PueueWrapper instance
pueue = PueueWrapper()


@app.get("/api/add")
async def add_task(command: str) -> str:
    """
    Add a task to Pueue asynchronously.
    """
    try:
        task_id = await pueue.add_task(command)
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
async def submit_and_wait(command: str) -> str:
    """
    Submit a task and wait for it asynchronously.
    """
    try:
        result = await pueue.submit_and_wait(command)
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


@app.get("/")
async def redirect_root_to_docs():
    return RedirectResponse("/docs")


if __name__ == "__main__":
    # python -m uvicorn api:app --reload
    # https://127.0.0.1:8000/docs
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
