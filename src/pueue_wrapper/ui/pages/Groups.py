"""
組管理頁面

管理 Pueue 任務組，包括創建、刪除、配置組
"""

import streamlit as st
import pandas as pd
from typing import Dict, Optional

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
    display_task_control_result,
)


def main():
    """組管理主頁面"""
    st.set_page_config(
        page_title="PueueWrapper UI - 組管理", page_icon="👥", layout="wide"
    )

    # 初始化
    init_session_state()

    # 標題
    st.title("👥 組管理")
    st.markdown("---")

    # 側邊欄配置
    config = setup_sidebar_config()

    # 主要內容區域
    tab1, tab2, tab3 = st.tabs(["📊 組概覽", "➕ 創建組", "🔧 組操作"])

    with tab1:
        _display_groups_overview()

    with tab2:
        _display_create_group()

    with tab3:
        _display_group_operations()


def _display_groups_overview():
    """顯示組概覽"""
    st.subheader("📊 組概覽")

    # 刷新按鈕
    refresh_button("groups_overview_refresh")

    # 獲取組和任務數據
    with st.spinner("正在加載組和任務數據..."):
        try:
            groups_data, status_data = async_runner.run(_get_groups_and_status_data())
            if groups_data is None or status_data is None:
                st.error("無法獲取組或任務數據")
                return
        except Exception as e:
            display_error(e)
            return

    if not groups_data:
        st.info("沒有可用的組")
        return

    # 計算每個組的任務統計
    group_stats = _calculate_group_statistics(groups_data, status_data.tasks)

    # 顯示組統計卡片
    cols = st.columns(len(groups_data))

    for i, (group_name, group) in enumerate(groups_data.items()):
        with cols[i % len(cols)]:
            stats = group_stats.get(group_name, {})

            # 組狀態顯示
            status_emoji = "🔄" if group.status == "Running" else "⏸️"
            st.metric(
                label=f"{status_emoji} {group_name}",
                value=f"{stats.get('running', 0)}/{group.parallel_tasks}",
                delta=f"排隊: {stats.get('queued', 0)}",
                help=f"運行中/並行槽位，排隊任務數",
            )

            st.write(f"總任務: {stats.get('total', 0)}")
            st.write(f"已完成: {stats.get('completed', 0)}")
            st.write(f"失敗: {stats.get('failed', 0)}")

    # 詳細組信息表格
    st.subheader("📋 詳細組信息")

    groups_table_data = []
    for group_name, group in groups_data.items():
        stats = group_stats.get(group_name, {})

        groups_table_data.append(
            {
                "組名": group_name,
                "狀態": "🔄 運行中" if group.status == "Running" else "⏸️ 暫停",
                "並行槽位": f"{stats.get('running', 0)}/{group.parallel_tasks}",
                "排隊任務": stats.get("queued", 0),
                "總任務": stats.get("total", 0),
                "已完成": stats.get("completed", 0),
                "失敗": stats.get("failed", 0),
                "成功率": (
                    f"{stats.get('success_rate', 0):.1f}%"
                    if stats.get("total", 0) > 0
                    else "N/A"
                ),
            }
        )

    if groups_table_data:
        df = pd.DataFrame(groups_table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

    # 組狀態圖表
    if len(groups_data) > 1:
        _display_groups_charts(group_stats)

    # 顯示最後刷新時間
    show_last_refresh()


def _display_create_group():
    """顯示創建組界面"""
    st.subheader("➕ 創建新組")

    # 組創建表單
    with st.form("create_group_form"):
        col1, col2 = st.columns(2)

        with col1:
            new_group_name = st.text_input(
                "組名 *",
                placeholder="例如: cpu_intensive",
                help="組名應該是唯一的，只能包含字母、數字和下劃線",
            )

        with col2:
            initial_parallel = st.number_input(
                "初始並行槽位",
                min_value=1,
                max_value=100,
                value=1,
                help="該組最多可以同時運行多少個任務",
            )

        group_description = st.text_area(
            "組描述（可選）",
            placeholder="描述這個組的用途...",
            help="幫助您記住這個組的用途",
        )

        submitted = st.form_submit_button("🚀 創建組", type="primary")

        if submitted:
            if new_group_name.strip():
                _create_new_group(
                    new_group_name.strip(), initial_parallel, group_description
                )
            else:
                st.error("請輸入組名")

    # 顯示組命名建議
    with st.expander("💡 組命名建議"):
        st.write(
            """
        **推薦的組命名方式:**
        - `cpu_intensive` - CPU 密集型任務
        - `io_heavy` - I/O 密集型任務
        - `gpu_tasks` - GPU 相關任務
        - `quick_jobs` - 快速任務
        - `long_running` - 長時間運行任務
        - `batch_processing` - 批處理任務
        - `test_env` - 測試環境任務
        
        **命名規則:**
        - 使用小寫字母和下劃線
        - 避免特殊字符和空格
        - 使用描述性名稱
        """
        )


def _display_group_operations():
    """顯示組操作界面"""
    st.subheader("🔧 組操作")

    # 獲取組數據
    with st.spinner("正在加載組數據..."):
        try:
            groups_data = async_runner.run(_get_groups_data())
            if groups_data is None:
                st.error("無法獲取組數據")
                return
        except Exception as e:
            display_error(e)
            return

    if not groups_data:
        st.info("沒有可用的組")
        return

    # 選擇要操作的組
    selected_group = st.selectbox(
        "選擇要操作的組",
        options=list(groups_data.keys()),
        format_func=lambda x: f"{x} ({'運行中' if groups_data[x].status == 'Running' else '暫停'})",
    )

    if selected_group:
        group = groups_data[selected_group]

        # 顯示選中組的詳細信息
        st.subheader(f"📋 組 '{selected_group}' 詳細信息")

        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**組名:** {selected_group}")
            st.write(
                f"**狀態:** {'🔄 運行中' if group.status == 'Running' else '⏸️ 暫停'}"
            )
            st.write(f"**並行槽位:** {group.parallel_tasks}")

        with col2:
            # 獲取該組的任務統計
            try:
                status_data = async_runner.run(_get_status_data())
                group_tasks = [
                    task
                    for task in status_data.tasks.values()
                    if task.group == selected_group
                ]
                running_count = sum(
                    1 for task in group_tasks if "Running" in task.status
                )
                queued_count = sum(1 for task in group_tasks if "Queued" in task.status)

                st.write(f"**正在運行任務:** {running_count}")
                st.write(f"**排隊任務:** {queued_count}")
                st.write(f"**總任務:** {len(group_tasks)}")
            except:
                st.write("**任務統計:** 無法獲取")

        # 組操作
        st.subheader("⚙️ 可用操作")

        col1, col2, col3 = st.columns(3)

        with col1:
            # 修改並行槽位
            st.write("**修改並行槽位:**")
            new_parallel = st.number_input(
                "新的並行槽位數",
                min_value=1,
                max_value=100,
                value=group.parallel_tasks,
                key=f"parallel_{selected_group}",
            )

            if st.button("💾 更新並行槽位", key=f"update_parallel_{selected_group}"):
                _update_group_parallel(selected_group, new_parallel)

        with col2:
            # 組控制
            st.write("**組控制:**")

            if group.status == "Running":
                if st.button("⏸️ 暫停組", key=f"pause_{selected_group}"):
                    _pause_group(selected_group)
            else:
                if st.button("▶️ 啟動組", key=f"start_{selected_group}"):
                    _start_group(selected_group)

            if st.button("🧹 清理組任務", key=f"clean_{selected_group}"):
                _clean_group(selected_group)

        with col3:
            # 危險操作
            st.write("**危險操作:**")
            st.warning("⚠️ 以下操作不可逆")

            if selected_group != "default":  # 不允許刪除默認組
                if st.button("🗑️ 刪除組", key=f"delete_{selected_group}"):
                    _delete_group(selected_group)
            else:
                st.info("默認組不能刪除")


def _calculate_group_statistics(groups_data: Dict, tasks: Dict) -> Dict:
    """計算組統計信息"""
    stats = {}

    for group_name in groups_data.keys():
        group_tasks = [task for task in tasks.values() if task.group == group_name]

        running = sum(1 for task in group_tasks if "Running" in task.status)
        queued = sum(1 for task in group_tasks if "Queued" in task.status)
        completed = sum(1 for task in group_tasks if "Done" in task.status)

        # 計算失敗任務
        failed = sum(
            1
            for task in group_tasks
            if "Done" in task.status
            and hasattr(task.status["Done"], "result")
            and task.status["Done"].result != "Success"
        )

        # 計算成功率
        success_rate = 0
        if completed > 0:
            success_rate = ((completed - failed) / completed) * 100

        stats[group_name] = {
            "total": len(group_tasks),
            "running": running,
            "queued": queued,
            "completed": completed,
            "failed": failed,
            "success_rate": success_rate,
        }

    return stats


def _display_groups_charts(group_stats: Dict):
    """顯示組統計圖表"""
    st.subheader("📊 組統計圖表")

    # 準備圖表數據
    chart_data = []
    for group_name, stats in group_stats.items():
        chart_data.append(
            {
                "組名": group_name,
                "運行中": stats.get("running", 0),
                "排隊中": stats.get("queued", 0),
                "已完成": stats.get("completed", 0),
                "失敗": stats.get("failed", 0),
            }
        )

    if chart_data:
        df = pd.DataFrame(chart_data)

        col1, col2 = st.columns(2)

        with col1:
            # 堆積柱狀圖
            st.write("**任務狀態分佈**")
            st.bar_chart(df.set_index("組名")[["運行中", "排隊中", "已完成", "失敗"]])

        with col2:
            # 成功率圖表
            st.write("**成功率對比**")
            success_rates = {
                name: stats.get("success_rate", 0)
                for name, stats in group_stats.items()
            }
            st.bar_chart(
                pd.DataFrame.from_dict(
                    success_rates, orient="index", columns=["成功率"]
                )
            )


async def _get_groups_and_status_data():
    """獲取組和狀態數據"""
    wrapper = st.session_state.pueue_wrapper
    groups = await wrapper.get_groups()
    status = await wrapper.get_status()
    return groups, status


async def _get_groups_data():
    """獲取組數據"""
    wrapper = st.session_state.pueue_wrapper
    return await wrapper.get_groups()


async def _get_status_data():
    """獲取狀態數據"""
    wrapper = st.session_state.pueue_wrapper
    return await wrapper.get_status()


def _create_new_group(group_name: str, parallel_tasks: int, description: str):
    """創建新組"""
    try:
        wrapper = st.session_state.pueue_wrapper

        # 創建組
        result = async_runner.run(wrapper.add_group(group_name))

        if result and result.success:
            # 設置並行槽位
            parallel_result = async_runner.run(
                wrapper.set_group_parallel(parallel_tasks, group_name)
            )

            if parallel_result and parallel_result.success:
                st.success(
                    f"組 '{group_name}' 創建成功！並行槽位設置為 {parallel_tasks}"
                )
                if description:
                    st.info(f"組描述: {description}")
                st.rerun()
            else:
                st.warning(f"組 '{group_name}' 創建成功，但設置並行槽位失敗")
                display_task_control_result(parallel_result)
        else:
            display_task_control_result(result)

    except Exception as e:
        display_error(e)


def _update_group_parallel(group_name: str, parallel_tasks: int):
    """更新組並行槽位"""
    try:
        wrapper = st.session_state.pueue_wrapper
        result = async_runner.run(
            wrapper.set_group_parallel(parallel_tasks, group_name)
        )
        display_task_control_result(result)
        if result and result.success:
            st.rerun()
    except Exception as e:
        display_error(e)


def _pause_group(group_name: str):
    """暫停組"""
    try:
        wrapper = st.session_state.pueue_wrapper
        result = async_runner.run(wrapper.pause_task([], group=group_name))
        display_task_control_result(result)
        if result and result.success:
            st.rerun()
    except Exception as e:
        display_error(e)


def _start_group(group_name: str):
    """啟動組"""
    try:
        wrapper = st.session_state.pueue_wrapper
        result = async_runner.run(wrapper.start_task([], group=group_name))
        display_task_control_result(result)
        if result and result.success:
            st.rerun()
    except Exception as e:
        display_error(e)


def _clean_group(group_name: str):
    """清理組任務"""
    try:
        wrapper = st.session_state.pueue_wrapper
        result = async_runner.run(wrapper.clean_tasks(group_name))
        display_task_control_result(result)
        if result and result.success:
            st.rerun()
    except Exception as e:
        display_error(e)


def _delete_group(group_name: str):
    """刪除組"""
    # 確認對話框
    st.warning(f"⚠️ 確認要刪除組 '{group_name}' 嗎？這將刪除該組中的所有任務！")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ 確認刪除", type="primary", key=f"confirm_delete_{group_name}"):
            try:
                wrapper = st.session_state.pueue_wrapper
                result = async_runner.run(wrapper.remove_group(group_name))
                display_task_control_result(result)
                if result and result.success:
                    st.rerun()
            except Exception as e:
                display_error(e)

    with col2:
        if st.button("❌ 取消", key=f"cancel_delete_{group_name}"):
            st.rerun()


if __name__ == "__main__":
    main()
