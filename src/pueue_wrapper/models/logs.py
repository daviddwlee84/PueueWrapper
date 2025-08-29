from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field, RootModel
from .base import TaskStatusInfo


class LogTask(BaseModel):
    """Log 响应中的任务信息"""

    id: int
    created_at: datetime
    original_command: str
    command: str
    path: str
    envs: Dict[str, Any] = Field(default_factory=dict)
    group: str
    dependencies: List[int] = Field(default_factory=list)
    priority: int
    label: Optional[str] = None
    status: Dict[
        str, TaskStatusInfo
    ]  # 状态类型到状态信息的映射，如 {"Done": TaskStatusInfo}


class TaskLogEntry(BaseModel):
    """单个任务的日志条目，包含任务信息和输出"""

    task: LogTask
    output: str


class PueueLogResponse(RootModel[Dict[str, TaskLogEntry]]):
    """pueue log -j 的完整响应"""

    def __iter__(self):
        """支持迭代"""
        return iter(self.root)

    def __getitem__(self, key: str) -> TaskLogEntry:
        """支持索引访问"""
        return self.root[key]

    def get(self, key: str, default=None) -> Optional[TaskLogEntry]:
        """支持 get 方法"""
        return self.root.get(key, default)

    def keys(self):
        """返回所有任务ID"""
        return self.root.keys()

    def values(self):
        """返回所有日志条目"""
        return self.root.values()

    def items(self):
        """返回所有键值对"""
        return self.root.items()

    def __len__(self) -> int:
        """返回任务数量"""
        return len(self.root)
