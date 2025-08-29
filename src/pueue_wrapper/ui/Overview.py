"""
PueueWrapper Streamlit UI - 主頁概覽

顯示 Pueue 任務隊列的整體狀態概覽
"""

import streamlit as st
import asyncio
from datetime import datetime
import pandas as pd
from pathlib import Path
import plotly.express as px
import plotly.graph_objects as go

# Import shared components
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
    """主頁面"""
    st.set_page_config(
        page_title="PueueWrapper UI - 概覽", page_icon="📊", layout="wide"
    )

    # 初始化
    init_session_state()

    # 標題
    st.title("📊 Pueue 任務隊列概覽")
    st.markdown("---")

    # 側邊欄配置
    config = setup_sidebar_config()

    # 刷新按鈕
    refresh_button("overview_refresh")

    # 獲取數據
    with st.spinner("正在加載數據..."):
        try:
            status = async_runner.run(_get_status_data())
            if status is None:
                st.error("無法獲取 Pueue 狀態數據")
                return
        except Exception as e:
            display_error(e)
            return

    # 顯示概覽數據
    _display_overview_metrics(status)

    # 顯示組狀態
    _display_groups_status(status)

    # 顯示最近任務
    _display_recent_tasks(status)

    # 顯示任務狀態分佈圖表
    _display_task_charts(status)

    # 快速操作面板
    _display_quick_actions()

    # 顯示最後刷新時間
    show_last_refresh()


async def _get_status_data():
    """獲取狀態數據"""
    wrapper = st.session_state.pueue_wrapper
    return await wrapper.get_status()


def _display_overview_metrics(status):
    """顯示概覽指標"""
    st.subheader("📈 系統概覽")

    # 計算統計數據
    total_tasks = len(status.tasks)
    running_tasks = sum(1 for task in status.tasks.values() if "Running" in task.status)
    completed_tasks = sum(1 for task in status.tasks.values() if "Done" in task.status)
    queued_tasks = sum(1 for task in status.tasks.values() if "Queued" in task.status)
    failed_tasks = sum(
        1
        for task in status.tasks.values()
        if "Done" in task.status
        and hasattr(task.status["Done"], "result")
        and task.status["Done"].result != "Success"
    )

    # 顯示指標卡片
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(label="總任務數", value=total_tasks, delta=None)

    with col2:
        st.metric(label="運行中", value=running_tasks, delta=None, delta_color="normal")

    with col3:
        st.metric(label="排隊中", value=queued_tasks, delta=None, delta_color="off")

    with col4:
        st.metric(
            label="已完成", value=completed_tasks, delta=None, delta_color="normal"
        )

    with col5:
        st.metric(label="失敗", value=failed_tasks, delta=None, delta_color="inverse")


def _display_groups_status(status):
    """顯示組狀態"""
    st.subheader("👥 組狀態")

    if not status.groups:
        st.info("沒有組信息")
        return

    # 創建組狀態數據
    groups_data = []
    for group_name, group in status.groups.items():
        # 計算該組的任務數量
        group_tasks = [
            task for task in status.tasks.values() if task.group == group_name
        ]
        running_count = sum(1 for task in group_tasks if "Running" in task.status)
        queued_count = sum(1 for task in group_tasks if "Queued" in task.status)

        groups_data.append(
            {
                "組名": group_name,
                "狀態": "🔄 運行中" if group.status == "Running" else "⏸️ 暫停",
                "並行槽位": f"{running_count}/{group.parallel_tasks}",
                "排隊任務": queued_count,
                "總任務": len(group_tasks),
            }
        )

    if groups_data:
        df = pd.DataFrame(groups_data)
        st.dataframe(df, use_container_width=True)


def _display_recent_tasks(status):
    """顯示最近任務"""
    st.subheader("🕒 最近任務")

    if not status.tasks:
        st.info("沒有任務")
        return

    # 獲取最近的 10 個任務
    tasks_list = list(status.tasks.items())
    recent_tasks = dict(tasks_list[-10:]) if len(tasks_list) > 10 else dict(tasks_list)

    # 創建任務數據框
    df = create_task_dataframe(recent_tasks)

    if not df.empty:
        # 使用 st.dataframe 顯示，支持排序和篩選
        st.dataframe(
            df,
            use_container_width=True,
            column_config={
                "ID": st.column_config.TextColumn("任務 ID", width="small"),
                "命令": st.column_config.TextColumn("命令", width="large"),
                "狀態": st.column_config.TextColumn("狀態", width="small"),
                "組": st.column_config.TextColumn("組", width="small"),
                "標籤": st.column_config.TextColumn("標籤", width="medium"),
                "創建時間": st.column_config.TextColumn("創建時間", width="medium"),
            },
            hide_index=True,
        )


def _display_task_charts(status):
    """顯示任務狀態分佈圖表"""
    st.subheader("📊 任務狀態分佈")

    if not status.tasks:
        st.info("沒有任務數據")
        return

    # 統計任務狀態
    status_counts = {}
    for task in status.tasks.values():
        status_key = list(task.status.keys())[0]
        status_counts[status_key] = status_counts.get(status_key, 0) + 1

    col1, col2 = st.columns(2)

    with col1:
        # 餅圖
        if status_counts:
            fig_pie = px.pie(
                values=list(status_counts.values()),
                names=list(status_counts.keys()),
                title="任務狀態分佈",
            )
            fig_pie.update_traces(textposition="inside", textinfo="percent+label")
            st.plotly_chart(fig_pie, use_container_width=True)

    with col2:
        # 柱狀圖
        if status_counts:
            fig_bar = px.bar(
                x=list(status_counts.keys()),
                y=list(status_counts.values()),
                title="任務狀態統計",
                labels={"x": "狀態", "y": "數量"},
            )
            st.plotly_chart(fig_bar, use_container_width=True)


def _display_quick_actions():
    """顯示快速操作面板"""
    st.subheader("⚡ 快速操作")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📝 提交任務", use_container_width=True):
            st.switch_page("pages/Submit_Task.py")

        if st.button("📋 任務狀態", use_container_width=True):
            st.switch_page("pages/Task_Status.py")

        if st.button("📜 查看日誌", use_container_width=True):
            st.switch_page("pages/Logs.py")

    with col2:
        if st.button("🔧 任務管理", use_container_width=True):
            st.switch_page("pages/Task_Management.py")

        if st.button("👥 組管理", use_container_width=True):
            st.switch_page("pages/Groups.py")

        if st.button("📝 任務模板", use_container_width=True):
            st.switch_page("pages/Task_Templates.py")

    with col3:
        if st.button("❓ 使用幫助", use_container_width=True):
            st.switch_page("pages/Help.py")

        st.markdown("---")

        # 版本信息
        st.caption("PueueWrapper UI v1.0")
        st.caption("Powered by Streamlit")


if __name__ == "__main__":
    main()
