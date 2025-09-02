"""
組統計頁面

顯示每個組的詳細統計信息，包括進度條和狀態分佈
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any

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
    get_status_colors,
    get_status_emoji,
    create_progress_bar_html,
    get_group_statistics_data,
)


def main():
    """組統計主頁面"""
    st.set_page_config(
        page_title="PueueWrapper UI - 組統計", page_icon="📊", layout="wide"
    )

    # 初始化
    init_session_state()

    # 標題
    st.title("📊 組統計分析")
    st.markdown("---")

    # 側邊欄配置
    config = setup_sidebar_config()

    # 顯示選項
    st.subheader("🎛️ 顯示選項")

    col1, col2, col3 = st.columns(3)

    with col1:
        show_progress_bars = st.checkbox("顯示進度條", value=True)

    with col2:
        show_detailed_breakdown = st.checkbox("顯示詳細分解", value=True)

    with col3:
        show_charts = st.checkbox("顯示圖表", value=True)

    # 顏色配置選項
    with st.expander("🎨 顏色和顯示配置"):
        col1, col2 = st.columns(2)

        with col1:
            st.write("**狀態顏色配置:**")
            colors = get_status_colors()
            emojis = get_status_emoji()

            for status, color in colors.items():
                if status in ["Failed", "Success"]:  # 跳過計算出的狀態
                    continue
                emoji = emojis.get(status, "❓")
                st.markdown(
                    f'<span style="color: {color}; font-size: 18px;">{emoji}</span> '
                    f'<span style="color: {color}; font-weight: bold;">{status}</span>',
                    unsafe_allow_html=True,
                )

        with col2:
            show_empty_groups = st.checkbox("顯示空組", value=False)
            sort_by = st.selectbox(
                "排序方式", options=["組名", "總任務數", "完成率", "失敗率"], index=0
            )

    # 刷新按鈕
    refresh_button("group_stats_refresh")

    # 獲取組統計數據
    with st.spinner("正在加載組統計數據..."):
        try:
            group_stats = async_runner.run(get_group_statistics_data())
            if not group_stats:
                st.info("沒有可用的組統計數據")
                return
        except Exception as e:
            display_error(e)
            return

    # 過濾空組
    if not show_empty_groups:
        group_stats = {
            name: stats for name, stats in group_stats.items() if stats.total_tasks > 0
        }

    if not group_stats:
        st.info("沒有符合條件的組")
        return

    # 排序組
    sorted_groups = _sort_groups(group_stats, sort_by)

    # 顯示總體概覽
    _display_overall_overview(group_stats)

    # 顯示每個組的統計
    _display_group_statistics(
        sorted_groups, show_progress_bars, show_detailed_breakdown
    )

    # 顯示圖表
    if show_charts:
        _display_statistics_charts(group_stats)

    # 顯示最後刷新時間
    show_last_refresh()


def _sort_groups(group_stats: Dict[str, Any], sort_by: str) -> Dict[str, Any]:
    """排序組"""
    if sort_by == "組名":
        return dict(sorted(group_stats.items()))
    elif sort_by == "總任務數":
        return dict(
            sorted(group_stats.items(), key=lambda x: x[1].total_tasks, reverse=True)
        )
    elif sort_by == "完成率":
        return dict(
            sorted(
                group_stats.items(), key=lambda x: x[1].completion_rate, reverse=True
            )
        )
    elif sort_by == "失敗率":
        return dict(
            sorted(group_stats.items(), key=lambda x: x[1].failure_rate, reverse=True)
        )
    else:
        return group_stats


def _display_overall_overview(group_stats: Dict[str, Any]):
    """顯示總體概覽"""
    st.subheader("📈 總體概覽")

    # 計算總體統計
    total_groups = len(group_stats)
    total_tasks = sum(stats.total_tasks for stats in group_stats.values())
    total_running = sum(stats.running_tasks for stats in group_stats.values())
    total_completed = sum(stats.completed_tasks for stats in group_stats.values())
    total_failed = sum(stats.failed_tasks for stats in group_stats.values())

    # 顯示指標卡片
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric("總組數", total_groups)

    with col2:
        st.metric("總任務數", total_tasks)

    with col3:
        st.metric("運行中", total_running, delta_color="normal")

    with col4:
        st.metric("已完成", total_completed, delta_color="normal")

    with col5:
        st.metric("失敗", total_failed, delta_color="inverse")

    # 總體進度條
    if total_tasks > 0:
        overall_stats = {
            "Running": total_running,
            "Queued": sum(stats.queued_tasks for stats in group_stats.values()),
            "Success": total_completed,
            "Failed": total_failed,
            "Paused": sum(stats.paused_tasks for stats in group_stats.values()),
            "Stashed": sum(stats.stashed_tasks for stats in group_stats.values()),
        }

        st.write("**總體進度:**")
        progress_html = create_progress_bar_html(
            overall_stats, total_tasks, show_labels=True
        )
        st.markdown(progress_html, unsafe_allow_html=True)


def _display_group_statistics(
    group_stats: Dict[str, Any], show_progress_bars: bool, show_detailed_breakdown: bool
):
    """顯示各組統計"""
    st.subheader("📋 各組詳細統計")

    for group_name, stats in group_stats.items():
        with st.container():
            st.subheader(f"👥 組: {group_name}")

            # 基本統計信息
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("總任務", stats.total_tasks)

            with col2:
                st.metric(
                    "完成率",
                    f"{stats.completion_rate:.1f}%",
                    delta_color="normal" if stats.completion_rate > 50 else "off",
                )

            with col3:
                st.metric(
                    "成功率",
                    f"{stats.success_rate:.1f}%",
                    delta_color="normal" if stats.success_rate > 80 else "inverse",
                )

            with col4:
                st.metric(
                    "失敗率",
                    f"{stats.failure_rate:.1f}%",
                    delta_color="inverse" if stats.failure_rate > 20 else "normal",
                )

            # 進度條
            if show_progress_bars and stats.total_tasks > 0:
                st.write("**任務狀態分佈:**")
                task_stats = {
                    "Running": stats.running_tasks,
                    "Queued": stats.queued_tasks,
                    "Success": stats.completed_tasks,
                    "Failed": stats.failed_tasks,
                    "Paused": stats.paused_tasks,
                    "Stashed": stats.stashed_tasks,
                }

                progress_html = create_progress_bar_html(
                    task_stats, stats.total_tasks, show_labels=True
                )
                st.markdown(progress_html, unsafe_allow_html=True)

            # 詳細分解
            if show_detailed_breakdown:
                with st.expander(f"📊 組 '{group_name}' 詳細分解"):
                    col1, col2 = st.columns(2)

                    with col1:
                        st.write("**任務狀態統計:**")
                        emojis = get_status_emoji()

                        st.write(f"{emojis['Running']} 運行中: {stats.running_tasks}")
                        st.write(f"{emojis['Queued']} 排隊中: {stats.queued_tasks}")
                        st.write(f"{emojis['Done']} 已完成: {stats.completed_tasks}")
                        st.write(f"{emojis['Failed']} 失敗: {stats.failed_tasks}")
                        st.write(f"{emojis['Paused']} 暫停: {stats.paused_tasks}")
                        st.write(f"{emojis['Stashed']} 暫存: {stats.stashed_tasks}")

                    with col2:
                        st.write("**計算比率:**")
                        st.write(f"📊 完成率: {stats.completion_rate:.2f}%")
                        st.write(f"✅ 成功率: {stats.success_rate:.2f}%")
                        st.write(f"❌ 失敗率: {stats.failure_rate:.2f}%")

                        # 效率指標
                        if stats.total_tasks > 0:
                            active_ratio = (
                                stats.running_tasks / stats.total_tasks
                            ) * 100
                            st.write(f"🔄 活躍率: {active_ratio:.2f}%")

                        # 添加時間詳細分析按鈕
                        if st.button(
                            f"⏱️ 查看 '{group_name}' 時間詳細分析",
                            key=f"time_details_{group_name}",
                            help="查看該組的詳細時間統計和分析",
                        ):
                            # 將組名存儲到 session state 中
                            st.session_state.selected_group_for_time_analysis = (
                                group_name
                            )
                            st.switch_page("pages/Group_Time_Details.py")

            st.markdown("---")


def _display_statistics_charts(group_stats: Dict[str, Any]):
    """顯示統計圖表"""
    st.subheader("📊 統計圖表")

    # 準備圖表數據
    chart_data = []
    for group_name, stats in group_stats.items():
        chart_data.append(
            {
                "組名": group_name,
                "總任務": stats.total_tasks,
                "運行中": stats.running_tasks,
                "排隊中": stats.queued_tasks,
                "已完成": stats.completed_tasks,
                "失敗": stats.failed_tasks,
                "暫停": stats.paused_tasks,
                "暫存": stats.stashed_tasks,
                "完成率": stats.completion_rate,
                "成功率": stats.success_rate,
                "失敗率": stats.failure_rate,
            }
        )

    if not chart_data:
        st.info("沒有數據可顯示圖表")
        return

    df = pd.DataFrame(chart_data)

    # 圖表選項
    col1, col2 = st.columns(2)

    with col1:
        chart_type = st.selectbox(
            "圖表類型",
            options=["任務狀態分佈", "完成率對比", "總任務數對比", "成功率 vs 失敗率"],
            index=0,
        )

    with col2:
        show_values = st.checkbox("顯示數值", value=True)

    # 根據選擇顯示不同圖表
    col1, col2 = st.columns(2)

    with col1:
        if chart_type == "任務狀態分佈":
            _create_status_distribution_chart(df, show_values)
        elif chart_type == "完成率對比":
            _create_completion_rate_chart(df, show_values)
        elif chart_type == "總任務數對比":
            _create_total_tasks_chart(df, show_values)
        elif chart_type == "成功率 vs 失敗率":
            _create_success_vs_failure_chart(df, show_values)

    with col2:
        # 總是顯示組統計表格
        st.write("**組統計數據表:**")
        display_df = df[["組名", "總任務", "完成率", "成功率", "失敗率"]].round(2)
        st.dataframe(display_df, use_container_width=True, hide_index=True)


def _create_status_distribution_chart(df: pd.DataFrame, show_values: bool):
    """創建狀態分佈圖表"""
    st.write("**任務狀態分佈**")

    # 堆積柱狀圖
    status_columns = ["運行中", "排隊中", "已完成", "失敗", "暫停", "暫存"]
    colors = ["#28a745", "#ffc107", "#6f42c1", "#dc3545", "#fd7e14", "#6c757d"]

    fig = go.Figure()

    for i, status in enumerate(status_columns):
        fig.add_trace(
            go.Bar(
                name=status,
                x=df["組名"],
                y=df[status],
                marker_color=colors[i % len(colors)],
                text=df[status] if show_values else None,
                textposition="inside",
            )
        )

    fig.update_layout(
        barmode="stack",
        title="各組任務狀態分佈",
        xaxis_title="組名",
        yaxis_title="任務數量",
        height=400,
    )

    st.plotly_chart(fig, use_container_width=True)


def _create_completion_rate_chart(df: pd.DataFrame, show_values: bool):
    """創建完成率對比圖表"""
    st.write("**完成率對比**")

    fig = px.bar(
        df,
        x="組名",
        y="完成率",
        title="各組完成率對比",
        color="完成率",
        color_continuous_scale="Viridis",
        text="完成率" if show_values else None,
    )

    if show_values:
        fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")

    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)


def _create_total_tasks_chart(df: pd.DataFrame, show_values: bool):
    """創建總任務數對比圖表"""
    st.write("**總任務數對比**")

    fig = px.bar(
        df,
        x="組名",
        y="總任務",
        title="各組總任務數對比",
        color="總任務",
        color_continuous_scale="Blues",
        text="總任務" if show_values else None,
    )

    if show_values:
        fig.update_traces(texttemplate="%{text}", textposition="outside")

    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)


def _create_success_vs_failure_chart(df: pd.DataFrame, show_values: bool):
    """創建成功率 vs 失敗率散點圖"""
    st.write("**成功率 vs 失敗率**")

    fig = px.scatter(
        df,
        x="成功率",
        y="失敗率",
        size="總任務",
        color="組名",
        title="成功率 vs 失敗率散點圖",
        hover_data=["總任務", "完成率"],
        text="組名" if show_values else None,
    )

    fig.update_layout(height=400)
    st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
