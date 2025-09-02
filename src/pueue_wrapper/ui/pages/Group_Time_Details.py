"""
組時間詳細統計頁面

展示每個組的詳細時間分析，包括運行時長分布、時間軸、效率分析等
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

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
    format_duration,
    format_datetime_detailed,
    create_duration_histogram_data,
    get_group_time_statistics_data,
    calculate_efficiency_score,
)


def main():
    """組時間詳細統計主頁面"""
    st.set_page_config(
        page_title="PueueWrapper UI - 組時間詳細統計", page_icon="⏱️", layout="wide"
    )

    # 初始化
    init_session_state()

    # 標題
    st.title("⏱️ 組時間詳細分析")
    st.markdown("---")

    # 側邊欄配置
    config = setup_sidebar_config()

    # 組選擇
    st.subheader("🎯 選擇要分析的組")

    # 獲取所有組
    try:
        with st.spinner("正在獲取組列表..."):
            wrapper = st.session_state.pueue_wrapper
            groups = async_runner.run(wrapper.get_groups())

        if not groups:
            st.info("沒有找到任何組")
            return

        group_names = list(groups.keys())

        # 檢查是否有預選的組
        default_index = 0
        if hasattr(st.session_state, "selected_group_for_time_analysis"):
            if st.session_state.selected_group_for_time_analysis in group_names:
                default_index = group_names.index(
                    st.session_state.selected_group_for_time_analysis
                )

        selected_group = st.selectbox(
            "選擇組",
            options=group_names,
            index=default_index,
            help="選擇要進行詳細時間分析的組",
        )

    except Exception as e:
        display_error(e)
        return

    # 刷新按鈕
    refresh_button("group_time_details_refresh")

    # 獲取時間統計數據
    with st.spinner(f"正在分析組 '{selected_group}' 的時間數據..."):
        try:
            time_stats = async_runner.run(
                get_group_time_statistics_data(selected_group)
            )
            if not time_stats or time_stats.successful_tasks_count == 0:
                st.info(f"組 '{selected_group}' 沒有成功完成的任務數據可供分析")
                return
        except Exception as e:
            display_error(e)
            return

    # 顯示統計概覽
    _display_overview_metrics(selected_group, time_stats)

    # 顯示時間區間分析
    _display_time_span_analysis(time_stats)

    # 顯示運行時長分析
    _display_duration_analysis(time_stats)

    # 顯示效率分析
    _display_efficiency_analysis(time_stats)

    # 顯示詳細圖表
    _display_detailed_charts(time_stats)

    # 顯示最後刷新時間
    show_last_refresh()


def _display_overview_metrics(group_name: str, time_stats):
    """顯示統計概覽"""
    st.subheader(f"📊 組 '{group_name}' 時間統計概覽")

    # 基本指標
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        st.metric(
            "成功任務數", time_stats.successful_tasks_count, help="成功完成的任務數量"
        )

    with col2:
        efficiency_score = calculate_efficiency_score(time_stats)
        st.metric(
            "效率評分",
            f"{efficiency_score:.0f}/100",
            delta=f"{efficiency_score - 70:.0f}" if efficiency_score != 70 else None,
            help="基於任務完成情況、穩定性和頻率的綜合評分",
        )

    with col3:
        st.metric(
            "平均運行時長",
            format_duration(time_stats.avg_duration),
            help="成功任務的平均運行時間",
        )

    with col4:
        st.metric(
            "任務完成頻率",
            f"{time_stats.tasks_per_hour:.1f}/小時",
            help="每小時完成的任務數",
        )

    with col5:
        st.metric(
            "平均排隊時間",
            format_duration(time_stats.average_queue_time),
            help="任務從入隊到開始執行的平均等待時間",
        )

    # 時間範圍信息
    if time_stats.earliest_start_time and time_stats.latest_end_time:
        st.info(
            f"📅 **分析時間範圍**: {format_datetime_detailed(time_stats.earliest_start_time)} "
            f"至 {format_datetime_detailed(time_stats.latest_end_time)} "
            f"({format_duration(time_stats.total_time_span)})"
        )


def _display_time_span_analysis(time_stats):
    """顯示時間區間分析"""
    st.subheader("🕐 時間區間分析")

    if not time_stats.earliest_start_time or not time_stats.latest_end_time:
        st.info("沒有足夠的時間數據進行區間分析")
        return

    col1, col2 = st.columns(2)

    with col1:
        st.write("**時間統計:**")
        st.write(
            f"⏰ **最早開始時間**: {format_datetime_detailed(time_stats.earliest_start_time)}"
        )
        st.write(
            f"🏁 **最後結束時間**: {format_datetime_detailed(time_stats.latest_end_time)}"
        )
        st.write(f"⏳ **總時間跨度**: {format_duration(time_stats.total_time_span)}")

        # 計算活躍時間比例
        if time_stats.avg_duration and time_stats.successful_tasks_count:
            total_work_time = (
                time_stats.avg_duration * time_stats.successful_tasks_count
            )
            activity_ratio = (
                (total_work_time / time_stats.total_time_span) * 100
                if time_stats.total_time_span > 0
                else 0
            )
            st.write(f"🎯 **活躍時間比例**: {activity_ratio:.1f}%")

    with col2:
        st.write("**失敗任務對比:**")
        if time_stats.failed_tasks_avg_duration:
            st.write(
                f"❌ **失敗任務平均時長**: {format_duration(time_stats.failed_tasks_avg_duration)}"
            )

            # 比較成功和失敗任務的運行時長
            if time_stats.avg_duration:
                ratio = time_stats.failed_tasks_avg_duration / time_stats.avg_duration
                if ratio > 1.2:
                    st.warning(f"⚠️ 失敗任務運行時間比成功任務長 {ratio:.1f}倍")
                elif ratio < 0.8:
                    st.info(f"ℹ️ 失敗任務比成功任務更快失敗（{ratio:.1f}倍）")
                else:
                    st.success(f"✅ 失敗和成功任務運行時間相近（{ratio:.1f}倍）")
        else:
            st.write("✅ 沒有失敗任務的時間數據")


def _display_duration_analysis(time_stats):
    """顯示運行時長分析"""
    st.subheader("📏 運行時長分布分析")

    if not time_stats.successful_tasks_count:
        st.info("沒有成功任務的運行時長數據")
        return

    # 基本統計
    col1, col2, col3 = st.columns(3)

    with col1:
        st.write("**基本統計:**")
        st.write(f"📊 **最短時長**: {format_duration(time_stats.min_duration)}")
        st.write(f"📊 **最長時長**: {format_duration(time_stats.max_duration)}")
        st.write(f"📊 **中位數**: {format_duration(time_stats.median_duration)}")
        st.write(f"📊 **標準差**: {format_duration(time_stats.std_duration)}")

    with col2:
        st.write("**百分位數:**")
        for percentile, value in time_stats.duration_percentiles.items():
            st.write(f"📈 **{percentile}**: {format_duration(value)}")

    with col3:
        st.write("**變異性分析:**")
        if time_stats.avg_duration and time_stats.std_duration:
            cv = time_stats.std_duration / time_stats.avg_duration
            st.write(f"📊 **變異係數**: {cv:.2f}")

            if cv < 0.2:
                st.success("✅ 運行時間非常穩定")
            elif cv < 0.5:
                st.info("ℹ️ 運行時間較為穩定")
            elif cv < 1.0:
                st.warning("⚠️ 運行時間波動較大")
            else:
                st.error("❌ 運行時間極不穩定")


def _display_efficiency_analysis(time_stats):
    """顯示效率分析"""
    st.subheader("⚡ 效率分析")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**吞吐量分析:**")
        st.write(f"🚀 **任務完成頻率**: {time_stats.tasks_per_hour:.2f} 任務/小時")

        if time_stats.tasks_per_hour >= 5:
            st.success("✅ 高效率：任務完成頻率很高")
        elif time_stats.tasks_per_hour >= 1:
            st.info("ℹ️ 中等效率：任務完成頻率適中")
        else:
            st.warning("⚠️ 低效率：任務完成頻率較低")

    with col2:
        st.write("**響應時間分析:**")
        if time_stats.average_queue_time is not None:
            st.write(
                f"⏱️ **平均排隊時間**: {format_duration(time_stats.average_queue_time)}"
            )

            if time_stats.average_queue_time < 60:
                st.success("✅ 響應迅速：排隊時間很短")
            elif time_stats.average_queue_time < 300:
                st.info("ℹ️ 響應良好：排隊時間適中")
            else:
                st.warning("⚠️ 響應較慢：排隊時間較長")
        else:
            st.write("ℹ️ 沒有排隊時間數據")


def _display_detailed_charts(time_stats):
    """顯示詳細圖表"""
    st.subheader("📊 詳細圖表分析")

    # 運行時長分布直方圖
    if time_stats.duration_buckets:
        st.write("**運行時長分布直方圖**")

        labels, values = create_duration_histogram_data(time_stats.duration_buckets)

        fig = go.Figure(
            data=[
                go.Bar(
                    x=labels,
                    y=values,
                    marker_color="skyblue",
                    text=values,
                    textposition="auto",
                )
            ]
        )

        fig.update_layout(
            title="任務運行時長分布",
            xaxis_title="運行時長區間",
            yaxis_title="任務數量",
            height=400,
        )

        st.plotly_chart(fig, use_container_width=True)

    # 百分位數可視化
    if time_stats.duration_percentiles:
        st.write("**運行時長百分位數分析**")

        percentiles = list(time_stats.duration_percentiles.keys())
        values = [time_stats.duration_percentiles[p] for p in percentiles]

        fig = go.Figure()

        fig.add_trace(
            go.Scatter(
                x=percentiles,
                y=values,
                mode="lines+markers",
                name="百分位數",
                line=dict(color="orange", width=3),
                marker=dict(size=8),
            )
        )

        # 添加平均線
        if time_stats.avg_duration:
            fig.add_hline(
                y=time_stats.avg_duration,
                line_dash="dash",
                line_color="red",
                annotation_text=f"平均值: {format_duration(time_stats.avg_duration)}",
            )

        # 添加中位數線
        if time_stats.median_duration:
            fig.add_hline(
                y=time_stats.median_duration,
                line_dash="dot",
                line_color="green",
                annotation_text=f"中位數: {format_duration(time_stats.median_duration)}",
            )

        fig.update_layout(
            title="運行時長百分位數分布",
            xaxis_title="百分位數",
            yaxis_title="運行時長（秒）",
            height=400,
        )

        st.plotly_chart(fig, use_container_width=True)

    # 效率指標雷達圖
    _create_efficiency_radar_chart(time_stats)


def _create_efficiency_radar_chart(time_stats):
    """創建效率指標雷達圖"""
    st.write("**效率指標雷達圖**")

    # 計算各項指標評分（0-100）
    scores = {}

    # 吞吐量評分
    if time_stats.tasks_per_hour >= 5:
        scores["吞吐量"] = 100
    elif time_stats.tasks_per_hour >= 2:
        scores["吞吐量"] = 80
    elif time_stats.tasks_per_hour >= 1:
        scores["吞吐量"] = 60
    else:
        scores["吞吐量"] = 40

    # 穩定性評分（基於變異係數）
    if time_stats.std_duration and time_stats.avg_duration:
        cv = time_stats.std_duration / time_stats.avg_duration
        if cv < 0.2:
            scores["穩定性"] = 100
        elif cv < 0.5:
            scores["穩定性"] = 80
        elif cv < 1.0:
            scores["穩定性"] = 60
        else:
            scores["穩定性"] = 40
    else:
        scores["穩定性"] = 50

    # 響應性評分（基於排隊時間）
    if time_stats.average_queue_time is not None:
        if time_stats.average_queue_time < 60:
            scores["響應性"] = 100
        elif time_stats.average_queue_time < 300:
            scores["響應性"] = 80
        elif time_stats.average_queue_time < 900:
            scores["響應性"] = 60
        else:
            scores["響應性"] = 40
    else:
        scores["響應性"] = 50

    # 數據量評分
    if time_stats.successful_tasks_count >= 50:
        scores["數據量"] = 100
    elif time_stats.successful_tasks_count >= 20:
        scores["數據量"] = 80
    elif time_stats.successful_tasks_count >= 10:
        scores["數據量"] = 60
    else:
        scores["數據量"] = 40

    # 創建雷達圖
    categories = list(scores.keys())
    values = list(scores.values())

    fig = go.Figure()

    fig.add_trace(
        go.Scatterpolar(
            r=values,
            theta=categories,
            fill="toself",
            name="效率指標",
            line_color="blue",
        )
    )

    fig.update_layout(
        polar=dict(radialaxis=dict(visible=True, range=[0, 100])),
        showlegend=True,
        title="組效率指標雷達圖",
        height=500,
    )

    st.plotly_chart(fig, use_container_width=True)

    # 顯示評分詳情
    col1, col2 = st.columns(2)

    with col1:
        st.write("**各項指標評分:**")
        for category, score in scores.items():
            if score >= 80:
                st.success(f"✅ {category}: {score}/100")
            elif score >= 60:
                st.info(f"ℹ️ {category}: {score}/100")
            else:
                st.warning(f"⚠️ {category}: {score}/100")

    with col2:
        overall_score = sum(scores.values()) / len(scores)
        st.write("**綜合評估:**")
        st.metric("總體效率評分", f"{overall_score:.0f}/100")

        if overall_score >= 85:
            st.success("🏆 優秀：組運行效率非常高")
        elif overall_score >= 70:
            st.info("👍 良好：組運行效率較好")
        elif overall_score >= 55:
            st.warning("⚠️ 一般：組運行效率有改進空間")
        else:
            st.error("❌ 較差：組運行效率需要優化")


if __name__ == "__main__":
    main()
