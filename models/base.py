"""
基础模型定义，供其他模块共享使用
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TaskStatusInfo(BaseModel):
    """任务状态信息，包含入队、开始、结束时间和结果"""

    enqueued_at: datetime
    start: Optional[datetime] = None  # Running/Queued 状态可能没有 start
    end: Optional[datetime] = None  # Running/Queued 状态可能没有 end
    result: Optional[str] = None  # Running/Queued 状态可能没有 result
