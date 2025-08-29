#!/usr/bin/env python3
"""
簡化的異步功能測試
"""

import asyncio
from loguru import logger
from pueue_wrapper import PueueWrapper


async def test_all_features():
    """完整測試所有新功能"""
    pueue = PueueWrapper()

    logger.info("=== 開始測試所有新功能 ===")

    try:
        # 1. 測試增強的 add_task 功能
        logger.info("1. 測試增強的 add_task 功能")

        # 確保測試組不存在
        try:
            await pueue.remove_group("test-group")
        except:
            pass

        # 創建測試組
        result = await pueue.add_group("test-group")
        if result.success:
            logger.info(f"✅ 創建組: {result.message}")
        else:
            logger.info(f"⚠️ 創建組: {result.message}")

        # 設置並行任務數
        result = await pueue.set_group_parallel(2, "test-group")
        logger.info(f"✅ 設置並行任務數: {result.message}")

        # 添加各種類型的任務
        task_id1 = await pueue.add_task(
            command="echo 'Hello from test-group'",
            label="test-task-1",
            working_directory="/tmp",
            group="test-group",
            priority=10,
        )
        logger.info(f"✅ 添加高優先級任務: {task_id1}")

        task_id2 = await pueue.add_task(
            command="echo 'Dependent task'",
            label="dependent-task",
            group="test-group",
            after=[int(task_id1)],
            priority=5,
        )
        logger.info(f"✅ 添加依賴任務: {task_id2}")

        # 添加暫存任務
        task_id3 = await pueue.add_task(
            command="echo 'Stashed task'", label="stashed-task", stashed=True
        )
        logger.info(f"✅ 添加暫存任務: {task_id3}")

        # 2. 測試 group 管理
        logger.info("\n2. 測試 group 管理功能")

        groups = await pueue.get_groups()
        for name, group in groups.items():
            logger.info(
                f"✅ 組 '{name}': 狀態={group.status}, 並行任務數={group.parallel_tasks}"
            )

        # 3. 測試狀態獲取
        logger.info("\n3. 測試狀態獲取")

        # 等待任務完成
        await asyncio.sleep(2)

        status = await pueue.get_status()
        task_ids = list(status.tasks.keys())
        logger.info(f"✅ 當前任務: {task_ids}")

        # 4. 測試任務控制
        logger.info("\n4. 測試任務控制功能")

        if task_ids:
            # 測試重啟任務
            result = await pueue.restart_task([int(task_ids[0])])
            logger.info(f"✅ 重啟任務: {result.message}")

            # 等待重啟任務完成
            await asyncio.sleep(1)

        # 5. 測試清理和重置
        logger.info("\n5. 測試清理和重置功能")

        # 清理任務
        result = await pueue.clean_tasks("test-group")
        logger.info(f"✅ 清理任務: {result.message}")

        # 檢查並重置組
        groups = await pueue.get_groups()
        if "test-group" in groups:
            result = await pueue.reset_queue(groups=["test-group"], force=True)
            logger.info(f"✅ 重置組: {result.message}")

            # 移除組
            result = await pueue.remove_group("test-group")
            logger.info(f"✅ 移除組: {result.message}")

        # 6. 測試日誌功能
        logger.info("\n6. 測試日誌功能")

        if task_ids:
            log_entry = await pueue.get_task_log_entry(task_ids[0])
            if log_entry:
                logger.info(
                    f"✅ 獲取任務日誌: 任務 {log_entry.task.id} - {log_entry.task.command}"
                )

            logs = await pueue.get_logs_json([task_ids[0]])
            logger.info(f"✅ 獲取結構化日誌: {len(logs)} 個任務")

        logger.info("\n🎉 所有功能測試完成！")

    except Exception as e:
        logger.error(f"❌ 測試過程中出現錯誤: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_all_features())
