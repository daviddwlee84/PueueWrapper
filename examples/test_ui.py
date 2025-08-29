#!/usr/bin/env python3
"""
PueueWrapper UI 測試腳本

用於測試 UI 功能的演示腳本
"""

import asyncio
import sys
from pathlib import Path

# 添加 src 路徑
sys.path.append(str(Path(__file__).parent.parent / "src"))

from pueue_wrapper.pueue_wrapper import PueueWrapper


async def create_demo_tasks():
    """創建一些演示任務"""
    wrapper = PueueWrapper()

    print("🚀 創建演示任務...")

    # 創建一些測試組
    try:
        await wrapper.add_group("demo")
        await wrapper.add_group("testing")
        print("✅ 創建演示組成功")
    except Exception as e:
        print(f"ℹ️  組可能已存在: {e}")

    # 提交各種類型的任務
    demo_tasks = [
        {
            "command": "echo 'Hello from PueueWrapper UI!'",
            "label": "greeting",
            "group": "demo",
        },
        {"command": "sleep 10", "label": "short_sleep", "group": "demo"},
        {
            "command": "echo 'Task 1' && sleep 2 && echo 'Task 1 Complete'",
            "label": "quick_task",
            "group": "testing",
        },
        {
            "command": "python -c \"import time; [print(f'Step {i}') or time.sleep(1) for i in range(5)]\"",
            "label": "python_demo",
            "group": "testing",
        },
        {"command": "ls -la", "label": "list_files", "group": "demo"},
        {
            "command": "date && echo 'Current date and time'",
            "label": "datetime_check",
            "group": "demo",
        },
    ]

    task_ids = []
    for task in demo_tasks:
        try:
            task_id = await wrapper.add_task(
                command=task["command"], label=task["label"], group=task["group"]
            )
            task_ids.append(task_id)
            print(f"✅ 創建任務 {task_id}: {task['label']}")
        except Exception as e:
            print(f"❌ 創建任務失敗: {e}")

    print(f"\n🎉 成功創建 {len(task_ids)} 個演示任務")
    print("📱 現在可以在 UI 中查看這些任務了！")

    # 顯示狀態
    try:
        status = await wrapper.get_status()
        print(f"\n📊 當前狀態:")
        print(f"   總任務數: {len(status.tasks)}")
        print(f"   可用組: {list(status.groups.keys())}")
    except Exception as e:
        print(f"❌ 獲取狀態失敗: {e}")

    return task_ids


async def clean_demo_tasks():
    """清理演示任務"""
    wrapper = PueueWrapper()

    print("🧹 清理演示任務...")

    try:
        # 清理已完成的任務
        await wrapper.clean_tasks("demo")
        await wrapper.clean_tasks("testing")
        print("✅ 清理已完成任務成功")

        # 可選：刪除演示組（注意：這會刪除組中的所有任務）
        # await wrapper.remove_group("demo")
        # await wrapper.remove_group("testing")
        # print("✅ 刪除演示組成功")

    except Exception as e:
        print(f"❌ 清理失敗: {e}")


def print_usage():
    """打印使用說明"""
    print(
        """
🎯 PueueWrapper UI 測試腳本

用法:
    python test_ui.py create    # 創建演示任務
    python test_ui.py clean     # 清理演示任務
    python test_ui.py help      # 顯示幫助

演示功能:
    - 創建不同類型的任務
    - 設置任務組和標籤
    - 測試各種任務狀態
    - 驗證 UI 功能

注意事項:
    - 確保 Pueue 守護進程正在運行 (pueued)
    - 確保已安裝 PueueWrapper 依賴
    - 任務會在 Pueue 中實際執行

UI 啟動:
    pueue-ui-server
    或
    streamlit run ui/Overview.py
    """
    )


async def main():
    """主函數"""
    if len(sys.argv) < 2:
        print_usage()
        return

    command = sys.argv[1].lower()

    if command == "create":
        await create_demo_tasks()
    elif command == "clean":
        await clean_demo_tasks()
    elif command == "help":
        print_usage()
    else:
        print(f"❌ 未知命令: {command}")
        print_usage()


if __name__ == "__main__":
    asyncio.run(main())
