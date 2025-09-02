from datetime import datetime
from typing import Dict, List, Optional, Union, Any
from pydantic import BaseModel, Field, RootModel
from .base import TaskStatusInfo, GroupStatus


class Task(BaseModel):
    """Status 响应中的任务信息"""

    id: int
    created_at: datetime
    original_command: str
    command: str
    path: str
    envs: Dict[str, str]
    group: str
    dependencies: List[int]
    priority: int
    label: Optional[str] = None
    status: Dict[
        str, TaskStatusInfo
    ]  # Using Dict directly to handle different status types


class Group(BaseModel):
    """任务组信息"""

    status: GroupStatus  # "Running", "Paused" 等
    parallel_tasks: int  # 并行任务数量


class PueueStatus(BaseModel):
    """pueue status --json 的完整响应"""

    tasks: Dict[str, Task]  # task_id 到 Task 的映射
    groups: Dict[str, Group]  # group_name 到 Group 的映射

    def get_task(self, task_id: str) -> Optional[Task]:
        """获取指定ID的任务"""
        return self.tasks.get(task_id)

    def get_group(self, group_name: str) -> Optional[Group]:
        """获取指定名称的组"""
        return self.groups.get(group_name)

    def get_running_tasks(self) -> Dict[str, Task]:
        """获取所有正在运行的任务"""
        return {
            task_id: task
            for task_id, task in self.tasks.items()
            if "Running" in task.status
        }

    def get_done_tasks(self) -> Dict[str, Task]:
        """获取所有已完成的任务"""
        return {
            task_id: task
            for task_id, task in self.tasks.items()
            if "Done" in task.status
        }

    def get_queued_tasks(self) -> Dict[str, Task]:
        """获取所有排队中的任务"""
        return {
            task_id: task
            for task_id, task in self.tasks.items()
            if "Queued" in task.status
        }

    def get_failed_tasks(self) -> Dict[str, Task]:
        """获取所有失败的任务"""
        return {
            task_id: task
            for task_id, task in self.tasks.items()
            if "Done" in task.status
            and self._is_task_failed(task.status["Done"].result)
        }

    @staticmethod
    def _is_task_failed(result: Any) -> bool:
        """检查任务是否失败"""
        if result is None:
            return True  # No result typically means failed
        if isinstance(result, str):
            return result != "Success"
        if isinstance(result, dict):
            # Failed tasks typically have {"Failed": exit_code} format
            return "Failed" in result
        return True  # Unknown format, assume failed

    def task_count_by_status(self) -> Dict[str, int]:
        """按状态统计任务数量"""
        status_counts = {}
        for task in self.tasks.values():
            status_type = next(iter(task.status))
            status_counts[status_type] = status_counts.get(status_type, 0) + 1
        return status_counts

    def __len__(self) -> int:
        """返回总任务数量"""
        return len(self.tasks)
