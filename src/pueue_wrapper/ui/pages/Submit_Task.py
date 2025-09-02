"""
提交任務頁面

支持異步提交任務和同步等待結果
"""

import streamlit as st
from datetime import datetime
from typing import Optional, List
import time

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
    display_success,
    add_submitted_task,
    update_submitted_task_status,
    get_submitted_tasks,
)


def main():
    """提交任務主頁面"""
    st.set_page_config(
        page_title="PueueWrapper UI - 提交任務", page_icon="📝", layout="wide"
    )

    # 初始化
    init_session_state()

    # 標題
    st.title("📝 提交任務")
    st.markdown("---")

    # 側邊欄配置
    config = setup_sidebar_config()

    # 主要內容區域
    tab1, tab2, tab3 = st.tabs(["📋 單個任務", "📚 批量任務", "📊 任務進度"])

    with tab1:
        _display_single_task_form(config)

    with tab2:
        _display_batch_task_form(config)

    with tab3:
        _display_task_progress()


def _display_single_task_form(config):
    """顯示單個任務提交表單"""
    st.subheader("🎯 單個任務提交")

    # 任務命令
    command = st.text_area(
        "任務命令 *",
        height=100,
        placeholder="例如: echo 'Hello World'",
        help="要執行的shell命令",
    )

    # 任務選項
    col1, col2 = st.columns(2)

    with col1:
        label = st.text_input(
            "任務標籤", placeholder="可選的任務標籤", help="給任務添加一個描述性標籤"
        )

        group = st.text_input(
            "任務組", value=config["default_group"], help="任務所屬的組"
        )

        priority = st.number_input(
            "優先級",
            min_value=-100,
            max_value=100,
            value=config["priority"],
            help="任務優先級，數字越大優先級越高",
        )

    with col2:
        working_dir = st.text_input(
            "工作目錄", value=config["working_dir"], help="任務執行的工作目錄"
        )

        delay = st.text_input(
            "延遲執行", placeholder="例如: 10s, 5m, 1h", help="延遲多長時間後執行任務"
        )

        after = st.text_input(
            "依賴任務ID",
            placeholder="例如: 1,2,3",
            help="等待這些任務完成後再執行，用逗號分隔",
        )

    # 高級選項
    with st.expander("🔧 高級選項"):
        col1, col2 = st.columns(2)

        with col1:
            immediate = st.checkbox(
                "立即開始",
                value=config["immediate_start"],
                help="添加任務後立即開始執行",
            )

            stashed = st.checkbox("暫存狀態", value=False, help="創建任務但不加入隊列")

        with col2:
            escape = st.checkbox(
                "轉義特殊字符",
                value=config["escape_shell"],
                help="自動轉義shell特殊字符",
            )

            follow = st.checkbox(
                "跟踪輸出", value=False, help="如果立即開始，是否跟踪輸出"
            )

    # 提交模式選擇
    st.subheader("🚀 提交模式")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📤 異步提交", use_container_width=True, type="primary"):
            if command.strip():
                _submit_async_task(
                    command,
                    label,
                    working_dir,
                    group,
                    priority,
                    _parse_dependencies(after),
                    delay,
                    immediate,
                    follow,
                    stashed,
                    escape,
                )
            else:
                st.error("請輸入任務命令")

    with col2:
        if st.button("⏳ 提交並等待", use_container_width=True):
            if command.strip():
                _submit_and_wait_task(
                    command,
                    label,
                    working_dir,
                    group,
                    priority,
                    _parse_dependencies(after),
                    delay,
                    stashed,
                    escape,
                )
            else:
                st.error("請輸入任務命令")

    with col3:
        if st.button("📄 提交並獲取輸出", use_container_width=True):
            if command.strip():
                _submit_and_get_output(
                    command,
                    label,
                    working_dir,
                    group,
                    priority,
                    _parse_dependencies(after),
                    delay,
                    stashed,
                    escape,
                )
            else:
                st.error("請輸入任務命令")


def _display_batch_task_form(config):
    """顯示批量任務提交表單"""
    st.subheader("📚 批量任務提交")

    # 批量命令輸入
    commands_text = st.text_area(
        "批量命令（每行一個）",
        height=200,
        placeholder="echo 'Task 1'\necho 'Task 2'\necho 'Task 3'",
        help="每行輸入一個命令，支持批量提交",
    )

    # 批量選項
    col1, col2 = st.columns(2)

    with col1:
        batch_label_prefix = st.text_input(
            "標籤前綴",
            placeholder="batch_task",
            help="批量任務的標籤前綴，會自動添加序號",
        )

        batch_group = st.text_input(
            "批量組", value=config["default_group"], help="批量任務所屬的組"
        )

    with col2:
        batch_priority = st.number_input(
            "批量優先級",
            min_value=-100,
            max_value=100,
            value=config["priority"],
            help="批量任務的優先級",
        )

        sequential = st.checkbox(
            "順序執行", value=False, help="讓每個任務等待前一個任務完成"
        )

    # 提交批量任務
    if st.button("🚀 提交批量任務", type="primary"):
        commands = [cmd.strip() for cmd in commands_text.split("\n") if cmd.strip()]
        if commands:
            _submit_batch_tasks(
                commands,
                batch_label_prefix,
                batch_group,
                batch_priority,
                sequential,
                config,
            )
        else:
            st.error("請輸入至少一個命令")


def _display_task_progress():
    """顯示任務進度"""
    st.subheader("📊 任務進度追蹤")

    # 刷新按鈕
    refresh_button("task_progress_refresh")

    # 獲取已提交的任務
    submitted_tasks = get_submitted_tasks()

    if not submitted_tasks:
        st.info("還沒有提交任何任務")
        return

    # 顯示任務進度
    for i, task_info in enumerate(reversed(submitted_tasks)):
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])

            with col1:
                st.write(f"**任務 {task_info['id']}**")
                st.code(
                    task_info["command"][:50] + "..."
                    if len(task_info["command"]) > 50
                    else task_info["command"]
                )

            with col2:
                st.write(f"**標籤:** {task_info.get('label', '無')}")
                st.write(
                    f"**提交時間:** {task_info['submitted_at'].strftime('%H:%M:%S')}"
                )

            with col3:
                status = task_info.get("status", "submitted")
                if status == "submitted":
                    st.warning("🔄 已提交")
                elif status == "running":
                    st.info("▶️ 運行中")
                elif status == "completed":
                    st.success("✅ 完成")
                elif status == "failed":
                    st.error("❌ 失敗")

            with col4:
                if st.button(f"📋 查看", key=f"view_{task_info['id']}"):
                    _show_task_details(task_info["id"])

            st.markdown("---")


def _parse_dependencies(after_str: str) -> Optional[List[int]]:
    """解析依賴任務ID"""
    if not after_str or not after_str.strip():
        return None

    try:
        return [int(x.strip()) for x in after_str.split(",") if x.strip()]
    except ValueError:
        st.error("依賴任務ID格式錯誤，請使用逗號分隔的數字")
        return None


def _submit_async_task(
    command,
    label,
    working_dir,
    group,
    priority,
    after,
    delay,
    immediate,
    follow,
    stashed,
    escape,
):
    """異步提交任務"""
    try:
        wrapper = st.session_state.pueue_wrapper

        # 提交任務
        task_id = async_runner.run(
            wrapper.add_task(
                command=command,
                label=label or None,
                working_directory=(
                    working_dir if working_dir != str(Path.home()) else None
                ),
                group=group if group != "default" else None,
                priority=priority if priority != 0 else None,
                after=after,
                delay=delay or None,
                immediate=immediate,
                follow=follow,
                stashed=stashed,
                escape=escape,
            )
        )

        if task_id:
            display_success(f"任務已成功提交！任務 ID: {task_id}")
            add_submitted_task(task_id, command, label)
            st.rerun()
        else:
            st.error("提交任務失敗")

    except Exception as e:
        display_error(e)


def _submit_and_wait_task(
    command, label, working_dir, group, priority, after, delay, stashed, escape
):
    """提交任務並等待完成"""
    try:
        wrapper = st.session_state.pueue_wrapper

        with st.spinner("正在提交任務並等待完成..."):
            # 先提交任務
            task_id = async_runner.run(
                wrapper.add_task(
                    command=command,
                    label=label or None,
                    working_directory=(
                        working_dir if working_dir != str(Path.home()) else None
                    ),
                    group=group if group != "default" else None,
                    priority=priority if priority != 0 else None,
                    after=after,
                    delay=delay or None,
                    stashed=stashed,
                    escape=escape,
                )
            )

            if task_id:
                add_submitted_task(task_id, command, label)
                st.info(f"任務已提交，ID: {task_id}，正在等待完成...")

                # 等待任務完成
                result = async_runner.run(wrapper.wait_for_task(task_id))

                if result:
                    display_success(f"任務 {task_id} 已完成！")
                    update_submitted_task_status(task_id, "completed")
                else:
                    st.error(f"等待任務 {task_id} 完成時發生錯誤")
                    update_submitted_task_status(task_id, "failed")

                st.rerun()
            else:
                st.error("提交任務失敗")

    except Exception as e:
        display_error(e)


def _submit_and_get_output(
    command, label, working_dir, group, priority, after, delay, stashed, escape
):
    """提交任務並獲取輸出"""
    try:
        wrapper = st.session_state.pueue_wrapper

        with st.spinner("正在提交任務並等待輸出..."):
            # 提交任務並等待輸出
            output = async_runner.run(
                wrapper.submit_and_wait_and_get_output(command, label)
            )

            if output is not None:
                display_success("任務完成！輸出如下：")
                st.subheader("📄 任務輸出")
                st.code(output, language="bash")
            else:
                st.error("獲取任務輸出失敗")

    except Exception as e:
        display_error(e)


def _submit_batch_tasks(commands, label_prefix, group, priority, sequential, config):
    """提交批量任務"""
    try:
        wrapper = st.session_state.pueue_wrapper

        with st.spinner(f"正在提交 {len(commands)} 個批量任務..."):
            previous_task_id = None
            submitted_count = 0

            for i, command in enumerate(commands):
                label = f"{label_prefix}_{i+1}" if label_prefix else None
                after = (
                    [int(previous_task_id)] if sequential and previous_task_id else None
                )

                task_id = async_runner.run(
                    wrapper.add_task(
                        command=command,
                        label=label,
                        group=group if group != "default" else None,
                        priority=priority if priority != 0 else None,
                        after=after,
                    )
                )

                if task_id:
                    add_submitted_task(task_id, command, label)
                    previous_task_id = task_id
                    submitted_count += 1
                else:
                    st.warning(f"第 {i+1} 個任務提交失敗: {command}")

            if submitted_count > 0:
                display_success(f"成功提交 {submitted_count}/{len(commands)} 個任務")
                st.rerun()
            else:
                st.error("所有批量任務提交失敗")

    except Exception as e:
        display_error(e)


def _show_task_details(task_id):
    """顯示任務詳細信息"""
    try:
        wrapper = st.session_state.pueue_wrapper

        # 獲取任務狀態
        status = async_runner.run(wrapper.get_status())

        if status and task_id in status.tasks:
            task = status.tasks[task_id]

            st.subheader(f"📋 任務 {task_id} 詳細信息")

            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**命令:** `{task.command}`")
                st.write(f"**狀態:** {list(task.status.keys())[0]}")
                st.write(f"**組:** {task.group}")
                st.write(f"**標籤:** {task.label or '無'}")

            with col2:
                st.write(f"**優先級:** {task.priority}")
                st.write(f"**創建時間:** {task.created_at or '無'}")

                # 從狀態信息中獲取時間信息
                if task.status:
                    status_key = list(task.status.keys())[0]
                    status_info = task.status[status_key]

                    if hasattr(status_info, "start") and status_info.start:
                        st.write(f"**開始時間:** {status_info.start}")
                    if hasattr(status_info, "end") and status_info.end:
                        st.write(f"**結束時間:** {status_info.end}")
        else:
            st.error(f"找不到任務 {task_id}")

    except Exception as e:
        display_error(e)


if __name__ == "__main__":
    main()
