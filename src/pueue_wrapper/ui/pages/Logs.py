"""
日誌查看頁面

顯示任務的執行日誌和輸出
"""

import streamlit as st
from datetime import datetime
from typing import Optional

# Import shared components
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from shared_components import (
    init_session_state,
    setup_sidebar_config,
    async_runner,
    refresh_button,
    show_last_refresh,
    display_error,
    format_datetime,
)


def main():
    """日誌查看主頁面"""
    st.set_page_config(
        page_title="PueueWrapper UI - 日誌查看", page_icon="📜", layout="wide"
    )

    # 初始化
    init_session_state()

    # 標題
    st.title("📜 任務日誌")
    st.markdown("---")

    # 側邊欄配置
    config = setup_sidebar_config()

    # 主要內容區域
    tab1, tab2 = st.tabs(["📋 所有日誌", "🔍 單個任務日誌"])

    with tab1:
        _display_all_logs()

    with tab2:
        _display_single_task_log()


def _display_all_logs():
    """顯示所有任務日誌"""
    st.subheader("📋 所有任務日誌")

    # 刷新按鈕
    refresh_button("all_logs_refresh")

    # 獲取日誌數據
    with st.spinner("正在加載日誌數據..."):
        try:
            logs = async_runner.run(_get_all_logs())
            if logs is None:
                st.error("無法獲取日誌數據")
                return
        except Exception as e:
            display_error(e)
            return

    if not logs:
        st.info("沒有日誌數據")
        return

    # 日誌篩選
    col1, col2, col3 = st.columns(3)

    with col1:
        # 按組篩選
        available_groups = set()
        for log_entry in logs.values():
            if hasattr(log_entry.task, "group"):
                available_groups.add(log_entry.task.group)

        selected_group = st.selectbox(
            "篩選組", options=["所有組"] + sorted(list(available_groups)), index=0
        )

    with col2:
        # 按狀態篩選
        show_only_completed = st.checkbox("只顯示已完成任務", value=False)

    with col3:
        # 日誌長度限制
        max_log_length = st.number_input(
            "日誌顯示長度限制", min_value=100, max_value=10000, value=500, step=100
        )

    # 篩選和顯示日誌
    filtered_logs = {}
    for task_id, log_entry in logs.items():
        # 組篩選
        if (
            selected_group != "所有組"
            and hasattr(log_entry.task, "group")
            and log_entry.task.group != selected_group
        ):
            continue

        # 狀態篩選
        if show_only_completed and hasattr(log_entry.task, "status"):
            task_status = (
                list(log_entry.task.status.keys())[0] if log_entry.task.status else ""
            )
            if task_status != "Done":
                continue

        filtered_logs[task_id] = log_entry

    if not filtered_logs:
        st.info("沒有符合條件的日誌")
        return

    # 顯示日誌列表
    for task_id, log_entry in filtered_logs.items():
        with st.expander(f"任務 {task_id}: {log_entry.task.command[:50]}..."):
            _display_log_entry(task_id, log_entry, max_log_length)

    # 顯示最後刷新時間
    show_last_refresh()


def _display_single_task_log():
    """顯示單個任務日誌"""
    st.subheader("🔍 單個任務日誌")

    # 獲取任務列表
    with st.spinner("正在加載任務列表..."):
        try:
            status = async_runner.run(_get_status_data())
            if status is None:
                st.error("無法獲取任務狀態")
                return
        except Exception as e:
            display_error(e)
            return

    if not status.tasks:
        st.info("當前沒有任務")
        return

    # 任務選擇
    task_options = {
        task_id: f"任務 {task_id}: {task.command[:50]}..."
        for task_id, task in status.tasks.items()
    }

    selected_task_id = st.selectbox(
        "選擇要查看日誌的任務",
        options=list(task_options.keys()),
        format_func=lambda x: task_options[x],
    )

    if selected_task_id:
        # 選項
        col1, col2 = st.columns(2)

        with col1:
            log_format = st.radio(
                "日誌格式", options=["結構化日誌", "純文本日誌"], index=0
            )

        with col2:
            auto_refresh_log = st.checkbox(
                "自動刷新日誌", value=False, help="每5秒自動刷新日誌"
            )

        # 刷新按鈕
        if st.button("🔄 刷新日誌") or auto_refresh_log:
            st.rerun()

        # 獲取單個任務日誌
        with st.spinner("正在加載任務日誌..."):
            try:
                if log_format == "結構化日誌":
                    log_entry = async_runner.run(_get_single_task_log(selected_task_id))
                    if log_entry:
                        _display_log_entry(selected_task_id, log_entry)
                    else:
                        st.warning("無法獲取結構化日誌")
                else:
                    log_text = async_runner.run(_get_task_log_text(selected_task_id))
                    if log_text:
                        st.subheader(f"任務 {selected_task_id} 純文本日誌")
                        st.code(log_text, language="bash")
                    else:
                        st.warning("無法獲取純文本日誌")
            except Exception as e:
                display_error(e)

        # 自動刷新
        if auto_refresh_log:
            import time

            time.sleep(5)
            st.rerun()


def _display_log_entry(task_id: str, log_entry, max_length: Optional[int] = None):
    """顯示日誌條目"""
    task = log_entry.task

    # 任務基本信息
    col1, col2 = st.columns(2)

    with col1:
        st.write(f"**任務 ID:** {task_id}")
        st.write(f"**命令:** `{task.command}`")
        if hasattr(task, "label") and task.label:
            st.write(f"**標籤:** {task.label}")
        if hasattr(task, "group"):
            st.write(f"**組:** {task.group}")

    with col2:
        if hasattr(task, "created_at") and task.created_at:
            st.write(f"**創建時間:** {format_datetime(task.created_at)}")
        if hasattr(task, "start") and task.start:
            st.write(f"**開始時間:** {format_datetime(task.start)}")
        if hasattr(task, "end") and task.end:
            st.write(f"**結束時間:** {format_datetime(task.end)}")
        if hasattr(task, "path") and task.path:
            st.write(f"**工作目錄:** {task.path}")

    # 任務狀態
    if hasattr(task, "status") and task.status:
        status_key = list(task.status.keys())[0]
        status_info = task.status[status_key]

        if status_key == "Done" and hasattr(status_info, "result"):
            if status_info.result == "Success":
                st.success(f"✅ 任務成功完成")
            else:
                st.error(f"❌ 任務執行失敗: {status_info.result}")
        elif status_key == "Running":
            st.info("🔄 任務正在運行")
        else:
            st.info(f"📋 任務狀態: {status_key}")

    # 原始命令
    if (
        hasattr(task, "original_command")
        and task.original_command
        and task.original_command != task.command
    ):
        st.write("**原始命令:**")
        st.code(task.original_command, language="bash")

    # 任務輸出
    if log_entry.output:
        st.write("**任務輸出:**")

        output = log_entry.output
        if max_length and len(output) > max_length:
            st.warning(f"日誌內容過長，只顯示前 {max_length} 個字符")
            output = output[:max_length] + "\n\n... (輸出被截斷) ..."

        # 嘗試檢測輸出格式
        if output.strip().startswith("{") or output.strip().startswith("["):
            # 可能是JSON
            try:
                import json

                json.loads(output)
                st.code(output, language="json")
            except:
                st.code(output, language="bash")
        else:
            st.code(output, language="bash")

        # 下載日誌按鈕
        st.download_button(
            label="📥 下載完整日誌",
            data=log_entry.output,
            file_name=f"task_{task_id}_log.txt",
            mime="text/plain",
        )
    else:
        st.info("沒有輸出日誌")


async def _get_all_logs():
    """獲取所有日誌"""
    wrapper = st.session_state.pueue_wrapper
    return await wrapper.get_logs_json()


async def _get_single_task_log(task_id: str):
    """獲取單個任務日誌"""
    wrapper = st.session_state.pueue_wrapper
    return await wrapper.get_task_log_entry(task_id)


async def _get_task_log_text(task_id: str):
    """獲取任務純文本日誌"""
    wrapper = st.session_state.pueue_wrapper
    return await wrapper.get_log(task_id)


async def _get_status_data():
    """獲取狀態數據"""
    wrapper = st.session_state.pueue_wrapper
    return await wrapper.get_status()


if __name__ == "__main__":
    main()
