#!/usr/bin/env python3
"""
示例: 如何使用 Status 相关的 Pydantic 数据模型

这个示例展示了如何优雅地处理 pueue status 的结构化数据。
"""

import asyncio
import json
from loguru import logger
from pueue_wrapper import PueueWrapper
from pueue_wrapper.models.status import PueueStatus, Task, Group
from pueue_wrapper.models.base import TaskStatusInfo


async def demo_status_models():
    """演示 Status 模型功能"""
    pueue = PueueWrapper()

    logger.info("=== Pueue Status 结构化数据模型演示 ===")

    # 1. 提交一些测试任务
    logger.info("1. 提交测试任务...")
    task1 = await pueue.add_task('echo "Status Demo Task 1"', "状态演示任务1")
    task2 = await pueue.add_task("sleep 3", "睡眠任务")
    task3 = await pueue.add_task('echo "Status Demo Task 3"', "状态演示任务3")
    task4 = await pueue.add_task("ls -la", "列表任务")

    logger.info(f"提交的任务ID: {[task1, task2, task3, task4]}")

    # 短暂等待，让一些任务开始执行
    await asyncio.sleep(1)

    # 2. 获取结构化的状态数据
    logger.info("2. 获取结构化状态数据...")
    status = await pueue.get_status()

    logger.info(f"总任务数: {len(status)}")
    logger.info(f"任务ID列表: {list(status.tasks.keys())}")

    # 3. 演示便利方法
    logger.info("3. 使用便利方法分析任务状态:")

    # 按状态分类任务
    running_tasks = status.get_running_tasks()
    done_tasks = status.get_done_tasks()
    queued_tasks = status.get_queued_tasks()
    failed_tasks = status.get_failed_tasks()

    logger.info(f"正在运行的任务: {list(running_tasks.keys())}")
    logger.info(f"已完成的任务: {list(done_tasks.keys())}")
    logger.info(f"排队中的任务: {list(queued_tasks.keys())}")
    logger.info(f"失败的任务: {list(failed_tasks.keys())}")

    # 状态统计
    status_counts = status.task_count_by_status()
    logger.info(f"任务状态统计: {status_counts}")

    # 4. 详细分析每个任务
    logger.info("4. 详细分析任务信息:")
    for task_id, task in status.tasks.items():
        logger.info(f"\n--- 任务 {task_id} ---")
        logger.info(f"  命令: {task.original_command}")
        logger.info(f"  创建时间: {task.created_at}")
        logger.info(f"  工作目录: {task.path}")
        logger.info(f"  组: {task.group}")
        logger.info(f"  优先级: {task.priority}")
        logger.info(f"  标签: {task.label}")
        logger.info(f"  依赖: {task.dependencies}")

        # 获取状态详情
        status_type = next(iter(task.status))
        status_info = task.status[status_type]
        logger.info(f"  状态: {status_type}")

        if status_info.start:
            logger.info(f"  开始时间: {status_info.start}")
        if status_info.end:
            logger.info(f"  结束时间: {status_info.end}")
        if status_info.result:
            logger.info(f"  执行结果: {status_info.result}")

        # 计算执行时长
        if status_info.end and status_info.start:
            duration = status_info.end - status_info.start
            logger.info(f"  执行时长: {duration}")

    # 5. 分析任务组信息
    logger.info("5. 分析任务组信息:")
    for group_name, group in status.groups.items():
        logger.info(f"\n--- 组 {group_name} ---")
        logger.info(f"  状态: {group.status}")
        logger.info(f"  并行任务数: {group.parallel_tasks}")

    # 6. 演示单个任务查询
    logger.info("6. 演示单个任务查询:")
    if task1:
        task_detail = status.get_task(task1)
        if task_detail:
            logger.info(f"任务 {task1} 详情:")
            logger.info(f"  命令: {task_detail.command}")
            logger.info(f"  当前状态: {next(iter(task_detail.status))}")

    # 7. 等待所有任务完成后再次查看状态
    logger.info("7. 等待任务完成...")
    await asyncio.sleep(5)

    final_status = await pueue.get_status()
    final_counts = final_status.task_count_by_status()
    logger.info(f"最终状态统计: {final_counts}")

    return status


def demo_manual_status_parsing():
    """演示手动解析状态 JSON 数据"""
    logger.info("\n=== 手动解析状态数据演示 ===")

    # 模拟 pueue status --json 的响应数据
    sample_status = {
        "tasks": {
            "0": {
                "id": 0,
                "created_at": "2025-03-28T14:16:31.093632+08:00",
                "original_command": 'echo "Hello, Status!"',
                "command": 'echo "Hello, Status!"',
                "path": "/Users/test/PueueWrapper",
                "envs": {
                    "HOME": "/Users/test",
                    "PATH": "/usr/bin:/bin",
                },
                "group": "default",
                "dependencies": [],
                "priority": 0,
                "label": "测试任务",
                "status": {
                    "Done": {
                        "enqueued_at": "2025-03-28T14:16:31.093479+08:00",
                        "start": "2025-03-28T14:16:31.168760+08:00",
                        "end": "2025-03-28T14:16:31.471857+08:00",
                        "result": "Success",
                    }
                },
            },
            "1": {
                "id": 1,
                "created_at": "2025-03-28T14:16:33.128793+08:00",
                "original_command": "sleep 3",
                "command": "sleep 3",
                "path": "/Users/test/PueueWrapper",
                "envs": {},
                "group": "default",
                "dependencies": [],
                "priority": 0,
                "label": None,
                "status": {
                    "Running": {
                        "enqueued_at": "2025-03-28T14:16:33.128780+08:00",
                        "start": "2025-03-28T14:16:33.286039+08:00",
                        "end": "2025-03-28T14:16:36.606272+08:00",
                        "result": "Success",
                    }
                },
            },
        },
        "groups": {
            "default": {"status": "Running", "parallel_tasks": 1},
        },
    }

    # 使用 Pydantic 模型解析
    status = PueueStatus.model_validate(sample_status)

    # 演示使用
    logger.info(f"解析的状态数据包含 {len(status)} 个任务")

    # 使用便利方法
    running_tasks = status.get_running_tasks()
    done_tasks = status.get_done_tasks()
    logger.info(f"运行中任务: {list(running_tasks.keys())}")
    logger.info(f"已完成任务: {list(done_tasks.keys())}")

    # 获取特定任务
    task_0 = status.get_task("0")
    if task_0:
        logger.info(f"任务0状态: {next(iter(task_0.status))}")
        logger.info(f"任务0标签: {task_0.label}")

    # 组信息
    default_group = status.get_group("default")
    if default_group:
        logger.info(f"默认组状态: {default_group.status}")
        logger.info(f"默认组并行任务数: {default_group.parallel_tasks}")


async def demo_status_monitoring():
    """演示状态监控功能"""
    logger.info("\n=== 状态监控演示 ===")

    pueue = PueueWrapper()

    # 提交一个长时间运行的任务
    task_id = await pueue.add_task("sleep 5", "监控测试任务")
    logger.info(f"提交监控任务: {task_id}")

    # 每秒检查一次状态
    for i in range(7):
        status = await pueue.get_status()
        task = status.get_task(task_id) if task_id else None

        if task:
            status_type = next(iter(task.status))
            logger.info(f"第{i+1}秒 - 任务 {task_id} 状态: {status_type}")

            if status_type == "Done":
                status_info = task.status[status_type]
                logger.info(f"任务完成，结果: {status_info.result}")
                break
        else:
            logger.info(f"第{i+1}秒 - 任务 {task_id} 未找到")

        await asyncio.sleep(1)


async def main():
    """主函数"""
    try:
        # 演示基本状态功能
        await demo_status_models()

        # 演示手动解析
        demo_manual_status_parsing()

        # 演示状态监控
        await demo_status_monitoring()

        logger.info("\n✅ 所有状态演示完成!")

    except Exception as e:
        logger.error(f"演示过程中出错: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
