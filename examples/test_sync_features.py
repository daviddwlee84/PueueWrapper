#!/usr/bin/env python3
"""
同步功能測試
"""

from loguru import logger
from pueue_wrapper.pueue_sync_wrapper import PueueWrapperSync


def test_sync_features():
    """測試同步包裝器功能"""
    logger.info("=== 開始測試同步包裝器功能 ===")

    try:
        pueue_sync = PueueWrapperSync()

        # 1. 測試創建組
        logger.info("1. 測試 group 管理")

        result = pueue_sync.add_group("sync-test")
        if result.success:
            logger.info(f"✅ 創建組: {result.message}")
        else:
            logger.info(f"⚠️ 創建組: {result.message}")

        # 2. 測試設置並行任務數
        result = pueue_sync.set_group_parallel(3, "sync-test")
        logger.info(f"✅ 設置並行任務數: {result.message}")

        # 3. 測試添加任務
        logger.info("\n2. 測試添加任務")

        task_id = pueue_sync.add_task(
            command="echo 'Sync wrapper test'",
            label="sync-test-task",
            group="sync-test",
            working_directory="/tmp",
        )
        logger.info(f"✅ 添加任務: {task_id}")

        # 4. 測試獲取組信息
        logger.info("\n3. 測試狀態獲取")

        groups = pueue_sync.get_groups()
        for name, group in groups.items():
            logger.info(f"✅ 組 '{name}': {group.status}, 並行={group.parallel_tasks}")

        # 5. 測試狀態
        status = pueue_sync.get_status()
        logger.info(f"✅ 總任務數: {len(status.tasks)}")

        # 6. 測試任務控制
        logger.info("\n4. 測試任務控制")

        # 等待任務完成
        import time

        time.sleep(1)

        result = pueue_sync.clean_tasks("sync-test")
        logger.info(f"✅ 清理任務: {result.message}")

        # 7. 測試重置和移除組
        logger.info("\n5. 測試重置功能")

        result = pueue_sync.reset_queue(groups=["sync-test"], force=True)
        logger.info(f"✅ 重置組: {result.message}")

        result = pueue_sync.remove_group("sync-test")
        logger.info(f"✅ 移除組: {result.message}")

        logger.info("\n🎉 同步包裝器測試完成！")

    except Exception as e:
        logger.error(f"❌ 同步測試過程中出現錯誤: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    test_sync_features()
