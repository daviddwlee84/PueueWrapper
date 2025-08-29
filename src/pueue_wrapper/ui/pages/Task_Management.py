"""
任務管理頁面

提供任務的各種管理操作，包括暫停、開始、重啟、刪除、清理等
"""

import streamlit as st
import pandas as pd
from typing import List, Optional

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
    display_task_control_result,
)


def main():
    """任務管理主頁面"""
    st.set_page_config(
        page_title="PueueWrapper UI - 任務管理", page_icon="🔧", layout="wide"
    )

    # 初始化
    init_session_state()

    # 標題
    st.title("🔧 任務管理")
    st.markdown("---")

    # 側邊欄配置
    config = setup_sidebar_config()

    # 主要內容區域
    tab1, tab2, tab3, tab4 = st.tabs(
        ["🎛️ 任務控制", "🧹 批量操作", "📊 並行設置", "🗑️ 清理重置"]
    )

    with tab1:
        _display_task_control(config)

    with tab2:
        _display_batch_operations(config)

    with tab3:
        _display_parallel_settings(config)

    with tab4:
        _display_cleanup_reset(config)


def _display_task_control(config):
    """顯示任務控制面板"""
    st.subheader("🎛️ 單個任務控制")

    # 獲取當前任務列表
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
        "選擇要操作的任務",
        options=list(task_options.keys()),
        format_func=lambda x: task_options[x],
    )

    if selected_task_id:
        task = status.tasks[selected_task_id]

        # 顯示任務基本信息
        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**任務 ID:** {selected_task_id}")
            st.write(f"**命令:** `{task.command}`")
            st.write(f"**狀態:** {format_task_status(task)}")

        with col2:
            st.write(f"**組:** {task.group}")
            st.write(f"**標籤:** {task.label or '無'}")
            st.write(f"**優先級:** {task.priority}")

        # 操作按鈕
        st.subheader("可用操作")

        col1, col2, col3, col4 = st.columns(4)

        current_status = list(task.status.keys())[0]

        with col1:
            # 暫停/開始
            if current_status == "Running":
                if st.button("⏸️ 暫停任務", use_container_width=True):
                    _pause_task(selected_task_id)
            elif current_status in ["Paused", "Queued"]:
                if st.button("▶️ 開始任務", use_container_width=True):
                    _start_task(selected_task_id)

        with col2:
            # 重啟
            if current_status in ["Done", "Failed"]:
                if st.button("🔄 重啟任務", use_container_width=True):
                    _restart_task(selected_task_id)
            elif current_status == "Running":
                if st.button("🔄 重啟 (強制)", use_container_width=True):
                    _restart_task(selected_task_id, in_place=True)

        with col3:
            # 終止
            if current_status == "Running":
                if st.button("🛑 終止任務", use_container_width=True):
                    _kill_task(selected_task_id)

        with col4:
            # 刪除
            if current_status in ["Done", "Failed", "Paused", "Stashed"]:
                if st.button("🗑️ 刪除任務", use_container_width=True):
                    _remove_task(selected_task_id)


def _display_batch_operations(config):
    """顯示批量操作面板"""
    st.subheader("🧹 批量操作")

    # 獲取當前任務列表
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

    # 任務篩選
    col1, col2 = st.columns(2)

    with col1:
        filter_group = st.selectbox(
            "篩選組", options=["所有組"] + list(status.groups.keys()), index=0
        )

    with col2:
        filter_status = st.selectbox(
            "篩選狀態",
            options=["所有狀態", "Running", "Queued", "Done", "Paused", "Stashed"],
            index=0,
        )

    # 篩選任務
    filtered_tasks = {}
    for task_id, task in status.tasks.items():
        if filter_group != "所有組" and task.group != filter_group:
            continue
        if filter_status != "所有狀態" and filter_status not in task.status:
            continue
        filtered_tasks[task_id] = task

    if not filtered_tasks:
        st.info("沒有符合條件的任務")
        return

    # 顯示任務列表
    df = create_task_dataframe(filtered_tasks)

    if not df.empty:
        # 任務選擇
        selected_rows = st.dataframe(
            df[["ID", "命令", "狀態", "組", "標籤"]],
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="multi-row",
        )

        if selected_rows.selection.rows:
            selected_task_ids = [
                int(df.iloc[row]["ID"]) for row in selected_rows.selection.rows
            ]

            st.write(f"已選擇 {len(selected_task_ids)} 個任務: {selected_task_ids}")

            # 批量操作按鈕
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                if st.button("⏸️ 批量暫停", use_container_width=True):
                    _batch_pause_tasks(selected_task_ids)

            with col2:
                if st.button("▶️ 批量開始", use_container_width=True):
                    _batch_start_tasks(selected_task_ids)

            with col3:
                if st.button("🔄 批量重啟", use_container_width=True):
                    _batch_restart_tasks(selected_task_ids)

            with col4:
                if st.button("🗑️ 批量刪除", use_container_width=True):
                    _batch_remove_tasks(selected_task_ids)


def _display_parallel_settings(config):
    """顯示並行設置面板"""
    st.subheader("📊 並行任務設置")

    # 獲取組信息
    with st.spinner("正在加載組信息..."):
        try:
            groups = async_runner.run(_get_groups_data())
            if groups is None:
                st.error("無法獲取組信息")
                return
        except Exception as e:
            display_error(e)
            return

    if not groups:
        st.info("沒有可用的組")
        return

    # 顯示當前組設置
    st.write("**當前組設置:**")
    groups_data = []
    for group_name, group in groups.items():
        groups_data.append(
            {
                "組名": group_name,
                "狀態": "🔄 運行中" if group.status == "Running" else "⏸️ 暫停",
                "並行槽位": group.parallel_tasks,
            }
        )

    df = pd.DataFrame(groups_data)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # 修改並行設置
    st.subheader("🔧 修改並行設置")

    col1, col2, col3 = st.columns(3)

    with col1:
        selected_group = st.selectbox("選擇組", options=list(groups.keys()))

    with col2:
        new_parallel = st.number_input(
            "新的並行數量",
            min_value=1,
            max_value=100,
            value=(
                groups[selected_group].parallel_tasks if selected_group in groups else 1
            ),
        )

    with col3:
        if st.button("💾 應用設置", use_container_width=True, type="primary"):
            _set_group_parallel(selected_group, new_parallel)


def _display_cleanup_reset(config):
    """顯示清理和重置面板"""
    st.subheader("🗑️ 清理和重置")

    st.warning("⚠️ 以下操作可能是不可逆的，請謹慎操作！")

    # 清理已完成任務
    st.write("**清理已完成的任務:**")

    col1, col2 = st.columns(2)

    with col1:
        cleanup_group = st.selectbox(
            "選擇要清理的組",
            options=["所有組"] + _get_available_groups(),
            index=0,
            key="cleanup_group",
        )

    with col2:
        if st.button("🧹 清理已完成任務", use_container_width=True):
            group = None if cleanup_group == "所有組" else cleanup_group
            _clean_tasks(group)

    st.markdown("---")

    # 重置隊列
    st.write("**重置整個任務隊列:**")

    st.error("🚨 重置操作將刪除所有任務，包括正在運行的任務！")

    col1, col2 = st.columns(2)

    with col1:
        reset_groups = st.multiselect(
            "選擇要重置的組（留空表示重置所有組）", options=_get_available_groups()
        )

    with col2:
        force_reset = st.checkbox(
            "強制重置（不要確認）", value=False, help="跳過確認對話框"
        )

    if st.button("💥 重置隊列", type="primary"):
        groups_to_reset = reset_groups if reset_groups else None

        if not force_reset:
            if st.button("⚠️ 確認重置", type="secondary"):
                _reset_queue(groups_to_reset, force=True)
        else:
            _reset_queue(groups_to_reset, force=True)


async def _get_status_data():
    """獲取狀態數據"""
    wrapper = st.session_state.pueue_wrapper
    return await wrapper.get_status()


async def _get_groups_data():
    """獲取組數據"""
    wrapper = st.session_state.pueue_wrapper
    return await wrapper.get_groups()


def _get_available_groups():
    """獲取可用的組列表"""
    try:
        groups = async_runner.run(_get_groups_data())
        if groups:
            return list(groups.keys())
    except:
        pass
    return ["default"]


def _pause_task(task_id):
    """暫停任務"""
    try:
        wrapper = st.session_state.pueue_wrapper
        result = async_runner.run(wrapper.pause_task(int(task_id)))
        display_task_control_result(result)
        if result and result.success:
            st.rerun()
    except Exception as e:
        display_error(e)


def _start_task(task_id):
    """開始任務"""
    try:
        wrapper = st.session_state.pueue_wrapper
        result = async_runner.run(wrapper.start_task(int(task_id)))
        display_task_control_result(result)
        if result and result.success:
            st.rerun()
    except Exception as e:
        display_error(e)


def _restart_task(task_id, in_place=False):
    """重啟任務"""
    try:
        wrapper = st.session_state.pueue_wrapper
        result = async_runner.run(wrapper.restart_task(int(task_id), in_place=in_place))
        display_task_control_result(result)
        if result and result.success:
            st.rerun()
    except Exception as e:
        display_error(e)


def _kill_task(task_id):
    """終止任務"""
    try:
        wrapper = st.session_state.pueue_wrapper
        result = async_runner.run(wrapper.kill_task(int(task_id)))
        display_task_control_result(result)
        if result and result.success:
            st.rerun()
    except Exception as e:
        display_error(e)


def _remove_task(task_id):
    """刪除任務"""
    try:
        wrapper = st.session_state.pueue_wrapper
        result = async_runner.run(wrapper.remove_task(int(task_id)))
        display_task_control_result(result)
        if result and result.success:
            st.rerun()
    except Exception as e:
        display_error(e)


def _batch_pause_tasks(task_ids):
    """批量暫停任務"""
    try:
        wrapper = st.session_state.pueue_wrapper
        result = async_runner.run(wrapper.pause_task(task_ids))
        display_task_control_result(result)
        if result and result.success:
            st.rerun()
    except Exception as e:
        display_error(e)


def _batch_start_tasks(task_ids):
    """批量開始任務"""
    try:
        wrapper = st.session_state.pueue_wrapper
        result = async_runner.run(wrapper.start_task(task_ids))
        display_task_control_result(result)
        if result and result.success:
            st.rerun()
    except Exception as e:
        display_error(e)


def _batch_restart_tasks(task_ids):
    """批量重啟任務"""
    try:
        wrapper = st.session_state.pueue_wrapper
        result = async_runner.run(wrapper.restart_task(task_ids))
        display_task_control_result(result)
        if result and result.success:
            st.rerun()
    except Exception as e:
        display_error(e)


def _batch_remove_tasks(task_ids):
    """批量刪除任務"""
    try:
        wrapper = st.session_state.pueue_wrapper
        result = async_runner.run(wrapper.remove_task(task_ids))
        display_task_control_result(result)
        if result and result.success:
            st.rerun()
    except Exception as e:
        display_error(e)


def _set_group_parallel(group, parallel_tasks):
    """設置組並行數量"""
    try:
        wrapper = st.session_state.pueue_wrapper
        result = async_runner.run(wrapper.set_group_parallel(parallel_tasks, group))
        display_task_control_result(result)
        if result and result.success:
            st.rerun()
    except Exception as e:
        display_error(e)


def _clean_tasks(group):
    """清理已完成任務"""
    try:
        wrapper = st.session_state.pueue_wrapper
        result = async_runner.run(wrapper.clean_tasks(group))
        display_task_control_result(result)
        if result and result.success:
            st.rerun()
    except Exception as e:
        display_error(e)


def _reset_queue(groups, force=False):
    """重置隊列"""
    try:
        wrapper = st.session_state.pueue_wrapper
        result = async_runner.run(wrapper.reset_queue(groups, force=force))
        display_task_control_result(result)
        if result and result.success:
            st.rerun()
    except Exception as e:
        display_error(e)


if __name__ == "__main__":
    main()
