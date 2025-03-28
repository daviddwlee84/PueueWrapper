from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from pueue_wrapper import PueueWrapper

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


@app.get("/api/submit_and_wait/{command}")
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
async def get_status() -> str:
    """
    List the status of all tasks.
    """
    try:
        status = await pueue.get_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/log/{task_id}")
async def get_log(task_id: str) -> str:
    """
    Retrieve the log of a specific task.
    """
    try:
        log = await pueue.get_log(task_id)
        return log
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    # python -m uvicorn api:app --reload
    # https://127.0.0.1:8000/docs
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
