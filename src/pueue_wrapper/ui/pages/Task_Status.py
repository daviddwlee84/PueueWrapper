"""
任務狀態頁面

顯示所有任務的詳細狀態，支持按組篩選和排序
"""

import streamlit as st
import pandas as pd
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
    create_task_dataframe,
    format_task_status,
    refresh_button,
    show_last_refresh,
    display_error,
)


def main():
    """任務狀態主頁面"""
    st.set_page_config(
        page_title="PueueWrapper UI - 任務狀態", page_icon="📋", layout="wide"
    )

    # 初始化
    init_session_state()

    # 標題
    st.title("📋 任務狀態")
    st.markdown("---")

    # 側邊欄配置
    config = setup_sidebar_config()

    # 任務篩選選項
    st.subheader("🔍 篩選選項")
    col1, col2, col3 = st.columns(3)

    with col1:
        selected_group = st.selectbox(
            "選擇組", options=["所有組"] + _get_available_groups(), index=0
        )

    with col2:
        selected_status = st.selectbox(
            "任務狀態",
            options=["所有狀態", "Running", "Queued", "Done", "Paused", "Stashed"],
            index=0,
        )

    with col3:
        show_only_recent = st.checkbox("只顯示最近任務", value=False)

    # 刷新按鈕
    refresh_button("task_status_refresh")

    # 獲取任務數據
    with st.spinner("正在加載任務數據..."):
        try:
            status = async_runner.run(_get_status_data())
            if status is None:
                st.error("無法獲取任務狀態數據")
                return
        except Exception as e:
            display_error(e)
            return

    # 篩選任務
    filtered_tasks = _filter_tasks(
        status.tasks, selected_group, selected_status, show_only_recent
    )

    # 顯示任務統計
    _display_task_statistics(filtered_tasks)

    # 顯示任務列表
    _display_task_list(filtered_tasks)

    # 顯示詳細信息
    _display_task_details(filtered_tasks)

    # 顯示最後刷新時間
    show_last_refresh()


async def _get_status_data():
    """獲取狀態數據"""
    wrapper = st.session_state.pueue_wrapper
    return await wrapper.get_status()


def _get_available_groups():
    """獲取可用的組列表"""
    try:
        status = async_runner.run(_get_status_data())
        if status and status.groups:
            return list(status.groups.keys())
    except:
        pass
    return ["default"]


def _filter_tasks(tasks, selected_group, selected_status, show_only_recent):
    """篩選任務"""
    filtered = {}

    for task_id, task in tasks.items():
        # 組篩選
        if selected_group != "所有組" and task.group != selected_group:
            continue

        # 狀態篩選
        if selected_status != "所有狀態":
            task_status = list(task.status.keys())[0]
            if task_status != selected_status:
                continue

        filtered[task_id] = task

    # 只顯示最近任務
    if show_only_recent:
        items = list(filtered.items())
        filtered = dict(items[-20:])  # 最近 20 個任務

    return filtered


def _display_task_statistics(tasks):
    """顯示任務統計"""
    st.subheader("📊 任務統計")

    if not tasks:
        st.info("沒有符合條件的任務")
        return

    # 統計各種狀態的任務數量
    status_counts = {}
    for task in tasks.values():
        status_key = list(task.status.keys())[0]
        status_counts[status_key] = status_counts.get(status_key, 0) + 1

    # 顯示統計卡片
    cols = st.columns(len(status_counts) if status_counts else 1)

    for i, (status, count) in enumerate(status_counts.items()):
        with cols[i % len(cols)]:
            emoji = {
                "Running": "🔄",
                "Queued": "⏳",
                "Done": "✅",
                "Paused": "⏸️",
                "Stashed": "📦",
            }.get(status, "❓")

            st.metric(label=f"{emoji} {status}", value=count)


def _display_task_list(tasks):
    """顯示任務列表"""
    st.subheader("📝 任務列表")

    if not tasks:
        return

    # 創建任務數據框
    df = create_task_dataframe(tasks)

    if not df.empty:
        # 添加選擇功能
        selected_tasks = st.dataframe(
            df,
            use_container_width=True,
            column_config={
                "ID": st.column_config.TextColumn("任務 ID", width="small"),
                "命令": st.column_config.TextColumn("命令", width="large"),
                "狀態": st.column_config.TextColumn("狀態", width="small"),
                "組": st.column_config.TextColumn("組", width="small"),
                "標籤": st.column_config.TextColumn("標籤", width="medium"),
                "創建時間": st.column_config.TextColumn("創建時間", width="medium"),
                "優先級": st.column_config.NumberColumn("優先級", width="small"),
                "路徑": st.column_config.TextColumn("路徑", width="large"),
            },
            hide_index=True,
            on_select="rerun",
            selection_mode="multi-row",
        )

        # 快速操作按鈕
        if len(df) > 0:
            st.subheader("⚡ 快速操作")
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("🔄 重新開始所選任務"):
                    if selected_tasks.selection.rows:
                        _restart_selected_tasks(df, selected_tasks.selection.rows)

            with col2:
                if st.button("⏸️ 暫停所選任務"):
                    if selected_tasks.selection.rows:
                        _pause_selected_tasks(df, selected_tasks.selection.rows)

            with col3:
                if st.button("▶️ 開始所選任務"):
                    if selected_tasks.selection.rows:
                        _start_selected_tasks(df, selected_tasks.selection.rows)

            with col4:
                if st.button("🗑️ 刪除所選任務"):
                    if selected_tasks.selection.rows:
                        _remove_selected_tasks(df, selected_tasks.selection.rows)


def _display_task_details(tasks):
    """顯示任務詳細信息"""
    st.subheader("🔍 任務詳細信息")

    if not tasks:
        return

    # 選擇要查看詳情的任務
    task_ids = list(tasks.keys())
    selected_task_id = st.selectbox(
        "選擇任務查看詳情",
        options=task_ids,
        format_func=lambda x: f"任務 {x}: {tasks[x].command[:50]}...",
    )

    if selected_task_id:
        task = tasks[selected_task_id]

        # 顯示詳細信息
        col1, col2 = st.columns(2)

        with col1:
            st.write("**基本信息**")
            st.write(f"**ID:** {selected_task_id}")
            st.write(f"**命令:** `{task.command}`")
            st.write(f"**狀態:** {format_task_status(task)}")
            st.write(f"**組:** {task.group}")
            st.write(f"**標籤:** {task.label or '無'}")
            st.write(f"**優先級:** {task.priority}")

        with col2:
            st.write("**執行信息**")
            st.write(f"**工作目錄:** {task.path or '無'}")
            st.write(f"**創建時間:** {task.created_at or '無'}")

            # 從狀態信息中獲取開始和結束時間
            status_key = list(task.status.keys())[0]
            status_info = task.status[status_key]

            if hasattr(status_info, "start") and status_info.start:
                st.write(f"**開始時間:** {status_info.start}")
            if hasattr(status_info, "end") and status_info.end:
                st.write(f"**結束時間:** {status_info.end}")
            if hasattr(status_info, "enqueued_at") and status_info.enqueued_at:
                st.write(f"**入隊時間:** {status_info.enqueued_at}")

        # 顯示完整命令
        if task.original_command and task.original_command != task.command:
            st.write("**原始命令:**")
            st.code(task.original_command, language="bash")

        # 依賴關係
        if hasattr(task, "dependencies") and task.dependencies:
            st.write("**依賴任務:**")
            st.write(", ".join(map(str, task.dependencies)))


def _restart_selected_tasks(df, selected_rows):
    """重新開始所選任務"""
    task_ids = [int(df.iloc[row]["ID"]) for row in selected_rows]
    try:
        wrapper = st.session_state.pueue_wrapper
        result = async_runner.run(wrapper.restart_task(task_ids))
        if result and result.success:
            st.success(f"成功重新開始任務: {task_ids}")
            st.rerun()
        else:
            st.error(f"重新開始任務失敗: {result.message if result else '未知錯誤'}")
    except Exception as e:
        st.error(f"重新開始任務時發生錯誤: {str(e)}")


def _pause_selected_tasks(df, selected_rows):
    """暫停所選任務"""
    task_ids = [int(df.iloc[row]["ID"]) for row in selected_rows]
    try:
        wrapper = st.session_state.pueue_wrapper
        result = async_runner.run(wrapper.pause_task(task_ids))
        if result and result.success:
            st.success(f"成功暫停任務: {task_ids}")
            st.rerun()
        else:
            st.error(f"暫停任務失敗: {result.message if result else '未知錯誤'}")
    except Exception as e:
        st.error(f"暫停任務時發生錯誤: {str(e)}")


def _start_selected_tasks(df, selected_rows):
    """開始所選任務"""
    task_ids = [int(df.iloc[row]["ID"]) for row in selected_rows]
    try:
        wrapper = st.session_state.pueue_wrapper
        result = async_runner.run(wrapper.start_task(task_ids))
        if result and result.success:
            st.success(f"成功開始任務: {task_ids}")
            st.rerun()
        else:
            st.error(f"開始任務失敗: {result.message if result else '未知錯誤'}")
    except Exception as e:
        st.error(f"開始任務時發生錯誤: {str(e)}")


def _remove_selected_tasks(df, selected_rows):
    """刪除所選任務"""
    task_ids = [int(df.iloc[row]["ID"]) for row in selected_rows]

    # 確認對話框
    if st.button(f"確認刪除任務 {task_ids}？", type="primary"):
        try:
            wrapper = st.session_state.pueue_wrapper
            result = async_runner.run(wrapper.remove_task(task_ids))
            if result and result.success:
                st.success(f"成功刪除任務: {task_ids}")
                st.rerun()
            else:
                st.error(f"刪除任務失敗: {result.message if result else '未知錯誤'}")
        except Exception as e:
            st.error(f"刪除任務時發生錯誤: {str(e)}")


if __name__ == "__main__":
    main()
