#!/usr/bin/env python3
"""
Example demonstrating the new Pueue wrapper features.
"""

import asyncio
from loguru import logger
from pueue_wrapper import PueueWrapper


async def demo_new_features():
    """Demonstrate new PueueWrapper features."""
    pueue = PueueWrapper()

    logger.info("=== 演示新的 PueueWrapper 功能 ===")

    # 1. 演示增強的 add_task 功能
    logger.info("1. 測試增強的 add_task 功能")

    # 創建測試組
    result = await pueue.add_group("test-group")
    logger.info(f"創建組 'test-group': {result.message}")

    # 設置組的並行任務數
    result = await pueue.set_group_parallel(2, "test-group")
    logger.info(f"設置並行任務數: {result.message}")

    # 添加任務到指定組，設置工作目錄和優先級
    task_id1 = await pueue.add_task(
        command="echo 'Hello from test-group in /tmp'",
        label="test-task-1",
        working_directory="/tmp",
        group="test-group",
        priority=10,
    )
    logger.info(f"添加高優先級任務: {task_id1}")

    # 添加依賴任務
    task_id2 = await pueue.add_task(
        command="echo 'This runs after task 1'",
        label="dependent-task",
        group="test-group",
        after=[int(task_id1)],  # 依賴第一個任務
        priority=5,
    )
    logger.info(f"添加依賴任務: {task_id2}")

    # 添加延遲執行的任務
    task_id3 = await pueue.add_task(
        command="echo 'Delayed task'",
        label="delayed-task",
        delay="5s",
        stashed=True,  # 暫存狀態
    )
    logger.info(f"添加延遲任務: {task_id3}")

    # 2. 演示 group 管理
    logger.info("\n2. 測試 group 管理功能")

    groups = await pueue.get_groups()
    for name, group in groups.items():
        logger.info(
            f"組 '{name}': 狀態={group.status}, 並行任務數={group.parallel_tasks}"
        )

    # 3. 演示任務控制
    logger.info("\n3. 測試任務控制功能")

    # 等待任務完成
    await asyncio.sleep(2)

    # 獲取狀態
    status = await pueue.get_status()
    task_ids = list(status.tasks.keys())
    logger.info(f"當前任務: {task_ids}")

    # 演示重啟任務
    if task_ids:
        result = await pueue.restart_task([int(task_ids[0])])
        logger.info(f"重啟任務: {result.message}")

    # 演示清理任務
    result = await pueue.clean_tasks("test-group")
    logger.info(f"清理測試組任務: {result.message}")

    # 4. 演示 reset 功能
    logger.info("\n4. 測試 reset 功能")

    # 重置指定組
    result = await pueue.reset_queue("test-group")
    logger.info(f"重置測試組: {result.message}")

    # 清理測試組
    result = await pueue.remove_group("test-group")
    logger.info(f"移除測試組: {result.message}")

    logger.info("\n=== 所有功能測試完成 ===")


def demo_sync_wrapper():
    """演示同步包裝器的新功能。"""
    from pueue_wrapper.pueue_sync_wrapper import PueueWrapperSync

    logger.info("\n=== 演示同步包裝器新功能 ===")

    pueue_sync = PueueWrapperSync()

    # 創建組
    result = pueue_sync.add_group("sync-test")
    logger.info(f"同步創建組: {result.message}")

    # 添加任務
    task_id = pueue_sync.add_task(
        command="echo 'Sync wrapper test'",
        label="sync-test",
        group="sync-test",
        working_directory="/tmp",
    )
    logger.info(f"同步添加任務: {task_id}")

    # 獲取組信息
    groups = pueue_sync.get_groups()
    for name, group in groups.items():
        logger.info(f"組 '{name}': {group.status}, 並行={group.parallel_tasks}")

    # 清理
    pueue_sync.clean_tasks("sync-test")
    pueue_sync.remove_group("sync-test")

    logger.info("同步包裝器測試完成")


if __name__ == "__main__":
    # 運行異步示例
    asyncio.run(demo_new_features())

    # 運行同步示例
    demo_sync_wrapper()
