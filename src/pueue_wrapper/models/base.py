"""
基础模型定义，供其他模块共享使用
"""

from datetime import datetime
from typing import Optional, Dict, List
from pydantic import BaseModel
from enum import Enum


class TaskStatusInfo(BaseModel):
    """任务状态信息，包含入队、开始、结束时间和结果"""

    enqueued_at: datetime
    start: Optional[datetime] = None  # Running/Queued 状态可能没有 start
    end: Optional[datetime] = None  # Running/Queued 状态可能没有 end
    result: Optional[str] = None  # Running/Queued 状态可能没有 result


class GroupStatus(str, Enum):
    """Group status enum"""

    RUNNING = "Running"
    PAUSED = "Paused"


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
