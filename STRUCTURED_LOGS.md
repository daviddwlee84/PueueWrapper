# Pueue Log 结构化数据模型

本文档介绍如何使用新的 Pydantic 数据模型来优雅地处理 pueue log JSON 响应。

## 数据模型概览

### 核心模型

1. **`TaskStatusInfo`** - 任务状态信息
   - `enqueued_at`: 入队时间
   - `start`: 开始时间  
   - `end`: 结束时间
   - `result`: 执行结果 (如 "Success")

2. **`LogTask`** - 日志中的任务信息
   - `id`: 任务ID
   - `created_at`: 创建时间
   - `original_command`: 原始命令
   - `command`: 执行命令
   - `path`: 工作目录
   - `envs`: 环境变量
   - `group`: 任务组
   - `dependencies`: 依赖任务
   - `priority`: 优先级
   - `label`: 标签
   - `status`: 状态映射 (如 `{"Done": TaskStatusInfo}`)

3. **`TaskLogEntry`** - 单个任务的日志条目
   - `task`: LogTask 对象
   - `output`: 任务输出

4. **`PueueLogResponse`** - 完整的日志响应
   - 字典形式: `{task_id: TaskLogEntry}`
   - 支持迭代、索引访问、长度计算等

## 使用方法

### 1. 获取所有任务的结构化日志

```python
from pueue_wrapper import PueueWrapper

pueue = PueueWrapper()
logs = await pueue.get_logs_json()

# 遍历所有任务
for task_id, log_entry in logs.items():
    print(f"任务 {task_id}: {log_entry.task.command}")
    print(f"输出: {log_entry.output}")
```

### 2. 获取特定任务的日志

```python
# 获取单个任务
task_log = await pueue.get_task_log_entry("0")
if task_log:
    print(f"任务输出: {task_log.output}")
    print(f"执行状态: {next(iter(task_log.task.status))}")

# 获取多个特定任务
specific_logs = await pueue.get_logs_json(["0", "1", "2"])
```

### 3. 访问任务状态信息

```python
task_log = await pueue.get_task_log_entry("0")
if task_log:
    # 获取状态类型和详细信息
    status_type = next(iter(task_log.task.status))  # 如 "Done"
    status_info = task_log.task.status[status_type]
    
    print(f"状态: {status_type}")
    print(f"开始时间: {status_info.start}")
    print(f"结束时间: {status_info.end}")
    print(f"执行结果: {status_info.result}")
    
    # 计算执行时长
    duration = status_info.end - status_info.start
    print(f"执行时长: {duration}")
```

## API 端点

新增了以下 FastAPI 端点:

### 1. 获取所有任务的结构化日志
```
GET /api/logs/json?task_ids=1,2,3
```

可选参数:
- `task_ids`: 逗号分隔的任务ID列表

### 2. 获取单个任务的结构化日志
```
GET /api/log/{task_id}/json
```

返回 `TaskLogEntry` 对象。

### 3. 原有的文本格式日志 (保持兼容)
```
GET /api/log/{task_id}
```

返回纯文本格式的日志。

## 示例用法

查看 `example_usage.py` 文件获取完整的使用示例:

```bash
python example_usage.py
```

## 优势

1. **类型安全**: 使用 Pydantic 模型确保数据类型正确
2. **自动验证**: 自动验证 JSON 数据格式
3. **IDE 支持**: 完整的类型提示和自动补全
4. **易于使用**: 支持字典式访问和迭代
5. **向后兼容**: 保留原有的文本格式 API

## 数据结构示例

pueue log -j 的响应结构:

```json
{
  "0": {
    "task": {
      "id": 0,
      "created_at": "2025-03-28T14:16:31.093632+08:00",
      "original_command": "echo \"Hello, Pueue!\"",
      "command": "echo \"Hello, Pueue!\"",
      "path": "/Users/user/PueueWrapper",
      "envs": {},
      "group": "default",
      "dependencies": [],
      "priority": 0,
      "label": null,
      "status": {
        "Done": {
          "enqueued_at": "2025-03-28T14:16:31.093479+08:00",
          "start": "2025-03-28T14:16:31.168760+08:00",
          "end": "2025-03-28T14:16:31.471857+08:00",
          "result": "Success"
        }
      }
    },
    "output": "Hello, Pueue!"
  }
}
```

现在可以通过 `PueueLogResponse` 模型优雅地访问这些数据!
