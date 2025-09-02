"""
共享組件和配置

包含所有頁面都會用到的組件、配置和工具函數
"""

import streamlit as st
import asyncio
from typing import Optional, Dict, Any, List
from datetime import datetime
import pandas as pd
from pathlib import Path

# Import PueueWrapper and models
import sys

sys.path.append(str(Path(__file__).parent.parent / "src"))

from pueue_wrapper.pueue_wrapper import PueueWrapper
from pueue_wrapper.models.status import PueueStatus, Task
from pueue_wrapper.models.logs import PueueLogResponse, TaskLogEntry
from pueue_wrapper.models.base import TaskControl, GroupStatistics


# Initialize session state
def init_session_state():
    """初始化 Streamlit session state"""
    if "pueue_wrapper" not in st.session_state:
        st.session_state.pueue_wrapper = PueueWrapper()

    if "submitted_tasks" not in st.session_state:
        st.session_state.submitted_tasks = []

    if "last_refresh" not in st.session_state:
        st.session_state.last_refresh = datetime.now()


def setup_sidebar_config():
    """設置側邊欄通用配置"""
    st.sidebar.title("⚙️ 任務配置")

    # Working Directory
    working_dir = st.sidebar.text_input(
        "工作目錄",
        value=str(Path.cwd()),
        help="任務執行的工作目錄",
    )

    # Default Group
    default_group = st.sidebar.text_input(
        "默認組", value="default", help="新任務的默認組"
    )

    # Priority
    priority = st.sidebar.number_input(
        "優先級",
        min_value=-100,
        max_value=100,
        value=0,
        help="任務優先級 (數字越大優先級越高)",
    )

    # Auto refresh
    auto_refresh = st.sidebar.checkbox("自動刷新", value=True, help="自動刷新任務狀態")

    if auto_refresh:
        refresh_interval = st.sidebar.selectbox(
            "刷新間隔",
            options=[5, 10, 30, 60],
            index=1,
            format_func=lambda x: f"{x} 秒",
        )
    else:
        refresh_interval = None

    # Advanced options expander
    with st.sidebar.expander("🔧 高級選項"):
        escape_shell = st.checkbox(
            "轉義特殊字符", value=False, help="自動轉義 shell 特殊字符"
        )

        immediate_start = st.checkbox(
            "立即開始", value=False, help="添加任務後立即開始執行"
        )

        print_task_id = st.checkbox(
            "打印任務 ID", value=True, help="添加任務後打印任務 ID"
        )

    return {
        "working_dir": working_dir,
        "default_group": default_group,
        "priority": priority,
        "auto_refresh": auto_refresh,
        "refresh_interval": refresh_interval,
        "escape_shell": escape_shell,
        "immediate_start": immediate_start,
        "print_task_id": print_task_id,
    }


async def get_current_status(group: Optional[str] = None) -> PueueStatus:
    """獲取當前狀態"""
    wrapper = st.session_state.pueue_wrapper
    return await wrapper.get_status()


def format_task_status(task: Task) -> str:
    """格式化任務狀態顯示"""
    status_key = list(task.status.keys())[0]
    status_info = task.status[status_key]

    if status_key == "Done":
        if hasattr(status_info, "result"):
            if status_info.result == "Success":
                return "✅ 成功"
            else:
                return f"❌ 失敗 ({status_info.result})"
        return "✅ 完成"
    elif status_key == "Running":
        return "🔄 運行中"
    elif status_key == "Paused":
        return "⏸️ 暫停"
    elif status_key == "Queued":
        return "⏳ 排隊中"
    elif status_key == "Stashed":
        return "📦 暫存"
    else:
        return f"❓ {status_key}"


def format_datetime(dt_str: str) -> str:
    """格式化日期時間顯示"""
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    except:
        return dt_str


def create_task_dataframe(tasks: Dict[str, Task]) -> pd.DataFrame:
    """創建任務數據框"""
    if not tasks:
        return pd.DataFrame(columns=["ID", "命令", "狀態", "組", "標籤", "創建時間"])

    data = []
    for task_id, task in tasks.items():
        data.append(
            {
                "ID": task_id,
                "命令": (
                    task.command[:50] + "..."
                    if len(task.command) > 50
                    else task.command
                ),
                "狀態": format_task_status(task),
                "組": task.group,
                "標籤": task.label or "",
                "創建時間": format_datetime(task.created_at) if task.created_at else "",
                "優先級": task.priority,
                "路徑": task.path or "",
            }
        )

    return pd.DataFrame(data)


def display_error(error: Exception):
    """顯示錯誤信息"""
    st.error(f"錯誤：{str(error)}")


def display_success(message: str):
    """顯示成功信息"""
    st.success(message)


def display_task_control_result(result: TaskControl):
    """顯示任務控制結果"""
    if result.success:
        st.success(result.message)
        if result.task_ids:
            st.info(f"影響的任務 ID: {result.task_ids}")
    else:
        st.error(result.message)


async def run_async_function(func, *args, **kwargs):
    """運行異步函數的輔助函數"""
    try:
        # 檢查是否已經在事件循環中
        try:
            loop = asyncio.get_running_loop()
            # 如果已經在事件循環中，創建一個任務
            import concurrent.futures

            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, func(*args, **kwargs))
                return future.result()
        except RuntimeError:
            # 沒有運行的事件循環，直接運行
            return await func(*args, **kwargs)
    except Exception as e:
        st.error(f"執行異步函數時發生錯誤：{str(e)}")
        return None


def add_submitted_task(task_id: str, command: str, label: Optional[str] = None):
    """添加已提交的任務到 session state"""
    task_info = {
        "id": task_id,
        "command": command,
        "label": label,
        "submitted_at": datetime.now(),
        "status": "submitted",
    }
    st.session_state.submitted_tasks.append(task_info)


def update_submitted_task_status(task_id: str, status: str):
    """更新已提交任務的狀態"""
    for task in st.session_state.submitted_tasks:
        if task["id"] == task_id:
            task["status"] = status
            task["updated_at"] = datetime.now()
            break


def get_submitted_tasks() -> List[Dict[str, Any]]:
    """獲取已提交的任務列表"""
    return st.session_state.submitted_tasks


def clear_submitted_tasks():
    """清空已提交的任務列表"""
    st.session_state.submitted_tasks = []


# Async wrapper for Streamlit
class StreamlitAsyncRunner:
    """Streamlit 異步運行器"""

    @staticmethod
    def run(coro):
        """運行協程"""
        try:
            return asyncio.run(coro)
        except Exception as e:
            st.error(f"執行異步操作時發生錯誤：{str(e)}")
            return None


# Global async runner instance
async_runner = StreamlitAsyncRunner()


def refresh_button(key: str = "refresh") -> bool:
    """刷新按鈕"""
    col1, col2, col3 = st.columns([1, 1, 8])

    with col1:
        if st.button("🔄 刷新", key=key):
            st.session_state.last_refresh = datetime.now()
            st.rerun()
            return True

    with col2:
        if st.button("🗑️ 清空", key=f"clear_{key}"):
            clear_submitted_tasks()
            st.rerun()
            return True

    return False


def show_last_refresh():
    """顯示最後刷新時間"""
    st.caption(f"最後刷新：{st.session_state.last_refresh.strftime('%H:%M:%S')}")


# 組統計相關函數
def get_status_colors():
    """獲取任務狀態對應的顏色"""
    return {
        "Running": "#28a745",  # 綠色 - 運行中
        "Queued": "#ffc107",  # 黃色 - 排隊中
        "Done": "#6f42c1",  # 紫色 - 已完成
        "Paused": "#fd7e14",  # 橙色 - 暫停
        "Stashed": "#6c757d",  # 灰色 - 暫存
        "Failed": "#dc3545",  # 紅色 - 失敗
        "Success": "#28a745",  # 綠色 - 成功
    }


def get_status_emoji():
    """獲取任務狀態對應的表情符號"""
    return {
        "Running": "🔄",
        "Queued": "⏳",
        "Done": "✅",
        "Paused": "⏸️",
        "Stashed": "📦",
        "Failed": "❌",
        "Success": "✅",
    }


def create_progress_bar_html(
    stats: Dict[str, int], total: int, show_labels: bool = True
) -> str:
    """創建自定義的進度條HTML"""
    if total == 0:
        return "<div style='background-color: #f0f0f0; height: 30px; border-radius: 15px; display: flex; align-items: center; justify-content: center;'>無任務</div>"

    colors = get_status_colors()

    # 計算百分比
    segments = []
    for status, count in stats.items():
        if count > 0:
            percentage = (count / total) * 100
            color = colors.get(status, "#6c757d")
            segments.append(
                {
                    "status": status,
                    "count": count,
                    "percentage": percentage,
                    "color": color,
                }
            )

    # 生成HTML
    html_segments = []
    for segment in segments:
        html_segments.append(
            f'<div style="background-color: {segment["color"]}; '
            f'width: {segment["percentage"]}%; height: 100%; '
            f'display: inline-block;" '
            f'title="{segment["status"]}: {segment["count"]}"></div>'
        )

    progress_html = f"""
    <div style="background-color: #f0f0f0; height: 30px; border-radius: 15px; overflow: hidden; display: flex;">
        {''.join(html_segments)}
    </div>
    """

    if show_labels:
        label_items = []
        for segment in segments:
            emoji = get_status_emoji().get(segment["status"], "❓")
            label_items.append(
                f'<span style="margin-right: 15px;">'
                f'<span style="color: {segment["color"]}; font-weight: bold;">{emoji}</span> '
                f'{segment["status"]}: {segment["count"]} ({segment["percentage"]:.1f}%)'
                f"</span>"
            )

        labels_html = f"""
        <div style="margin-top: 10px; font-size: 12px;">
            {''.join(label_items)}
        </div>
        """
        progress_html += labels_html

    return progress_html


async def get_group_statistics_data():
    """獲取所有組的統計數據"""
    wrapper = st.session_state.pueue_wrapper

    # 獲取所有組
    groups = await wrapper.get_groups()
    if not groups:
        return {}

    # 為每個組獲取統計數據
    group_stats = {}
    for group_name in groups.keys():
        try:
            stats = await wrapper.get_group_statistics(group_name)
            group_stats[group_name] = stats
        except Exception as e:
            st.error(f"獲取組 '{group_name}' 統計失敗: {str(e)}")

    return group_stats
