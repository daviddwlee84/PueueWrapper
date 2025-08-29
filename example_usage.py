#!/usr/bin/env python3
"""
示例: 如何使用新的 Pydantic 数据模型来解析 pueue log JSON 响应

这个示例展示了如何优雅地处理 pueue log 的结构化数据。
"""

import asyncio
import json
from loguru import logger
from pueue_wrapper import PueueWrapper
from models import PueueLogResponse, TaskLogEntry


async def demo_structured_logs():
    """演示结构化日志功能"""
    pueue = PueueWrapper()

    logger.info("=== Pueue Log 结构化数据模型演示 ===")

    # 1. 提交一些测试任务
    logger.info("1. 提交测试任务...")
    task1 = await pueue.add_task('echo "Hello, World!"', "问候任务")
    task2 = await pueue.add_task('sleep 2 && echo "Done sleeping"', "睡眠任务")
    task3 = await pueue.add_task("ls -la", "列表任务")

    # 等待任务完成
    logger.info("2. 等待任务完成...")
    await asyncio.sleep(3)

    # 3. 获取所有日志的结构化数据
    logger.info("3. 获取结构化日志数据...")
    all_logs = await pueue.get_logs_json()

    logger.info(f"总共找到 {len(all_logs)} 个任务的日志")

    # 4. 遍历所有任务并显示结构化信息
    logger.info("4. 分析任务数据:")
    for task_id, log_entry in all_logs.items():
        task = log_entry.task
        logger.info(f"\n--- 任务 {task_id} ---")
        logger.info(f"  命令: {task.original_command}")
        logger.info(f"  创建时间: {task.created_at}")
        logger.info(f"  工作目录: {task.path}")
        logger.info(f"  组: {task.group}")
        logger.info(f"  优先级: {task.priority}")
        logger.info(f"  标签: {task.label}")

        # 获取状态信息
        status_type = next(iter(task.status))
        status_info = task.status[status_type]
        logger.info(f"  状态: {status_type}")
        logger.info(f"  开始时间: {status_info.start}")
        logger.info(f"  结束时间: {status_info.end}")
        logger.info(f"  结果: {status_info.result}")
        logger.info(f"  输出: {log_entry.output}")

    # 5. 获取特定任务的日志
    logger.info("\n5. 获取特定任务的日志:")
    if task1:
        task_log = await pueue.get_task_log_entry(task1)
        if task_log:
            logger.info(f"任务 {task1} 的输出: {task_log.output}")
            logger.info(
                f"任务执行时长: {task_log.task.status[next(iter(task_log.task.status))].end - task_log.task.status[next(iter(task_log.task.status))].start}"
            )

    # 6. 获取多个特定任务的日志
    logger.info("\n6. 获取多个特定任务的日志:")
    specific_logs = await pueue.get_logs_json([task1, task2])
    logger.info(f"获取了任务 {list(specific_logs.keys())} 的日志")

    # 7. 演示数据模型的便利方法
    logger.info("\n7. 演示数据模型的便利方法:")
    logger.info(f"日志响应支持的操作:")
    logger.info(f"  - len(all_logs): {len(all_logs)}")
    logger.info(f"  - list(all_logs.keys()): {list(all_logs.keys())}")
    logger.info(f"  - 支持迭代和索引访问")

    return all_logs


def demo_manual_parsing():
    """演示手动解析 JSON 数据"""
    logger.info("\n=== 手动解析演示 ===")

    # 模拟 pueue log -j 的响应数据
    sample_json = {
        "0": {
            "task": {
                "id": 0,
                "created_at": "2025-03-28T14:16:31.093632+08:00",
                "original_command": 'echo "Hello, Pueue!"',
                "command": 'echo "Hello, Pueue!"',
                "path": "/Users/test/PueueWrapper",
                "envs": {},
                "group": "default",
                "dependencies": [],
                "priority": 0,
                "label": None,
                "status": {
                    "Done": {
                        "enqueued_at": "2025-03-28T14:16:31.093479+08:00",
                        "start": "2025-03-28T14:16:31.168760+08:00",
                        "end": "2025-03-28T14:16:31.471857+08:00",
                        "result": "Success",
                    }
                },
            },
            "output": "Hello, Pueue!",
        }
    }

    # 使用 Pydantic 模型解析
    logs = PueueLogResponse.model_validate(sample_json)

    # 访问数据
    task_0 = logs["0"]
    logger.info(f"任务 0 输出: {task_0.output}")
    logger.info(f"任务 0 命令: {task_0.task.command}")
    logger.info(f"任务 0 状态: {next(iter(task_0.task.status))}")


async def main():
    """主函数"""
    try:
        # 演示结构化日志功能
        await demo_structured_logs()

        # 演示手动解析
        demo_manual_parsing()

        logger.info("\n✅ 所有演示完成!")

    except Exception as e:
        logger.error(f"演示过程中出错: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
