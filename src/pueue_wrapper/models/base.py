"""
基础模型定义，供其他模块共享使用
"""

from datetime import datetime
from typing import Optional, Dict, List, Any
from pydantic import BaseModel, Field, model_validator
from enum import StrEnum


class TaskStatusInfo(BaseModel):
    """任务状态信息，包含入队、开始、结束时间和结果"""

    enqueued_at: Optional[datetime] = None
    start: Optional[datetime] = None  # Running/Queued 状态可能没有 start
    end: Optional[datetime] = None  # Running/Queued 状态可能没有 end
    result: Optional[str] = None  # Running/Queued 状态可能没有 result

    @model_validator(mode="before")
    @classmethod
    def handle_enqueue_fields(cls, data: Any) -> Any:
        """Handle both 'enqueued_at' and 'enqueue_at' field names"""
        if isinstance(data, dict):
            # If we have 'enqueue_at' but not 'enqueued_at', use 'enqueue_at'
            if "enqueue_at" in data and "enqueued_at" not in data:
                data["enqueued_at"] = data["enqueue_at"]
        return data


class GroupStatus(StrEnum):
    """Group status enum"""

    RUNNING = "Running"
    PAUSED = "Paused"
    RESET = "Reset"


class Group(BaseModel):
    """Group model"""

    status: GroupStatus
    parallel_tasks: int


class TaskAddOptions(BaseModel):
    """Options for adding a task"""

    working_directory: Optional[str] = None
    escape: bool = False
    immediate: bool = False
    follow: bool = False
    stashed: bool = False
    delay: Optional[str] = None
    group: Optional[str] = None
    after: Optional[List[int]] = None
    priority: Optional[int] = None
    label: Optional[str] = None
    print_task_id: bool = False


class TaskControl(BaseModel):
    """Task control operation result"""

    success: bool
    message: Optional[str] = None
    task_ids: Optional[List[int]] = None
