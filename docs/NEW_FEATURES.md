# PueueWrapper 新功能實現總結

## 概述

基於對 Pueue CLI 功能的深入分析，我們實現了一系列重要的新功能，大幅增強了 PueueWrapper 的能力。

## 實現的功能

### 1. 增強的 add_task 功能

現在 `add_task` 方法支持所有 Pueue CLI 的參數：

```python
task_id = await pueue.add_task(
    command="echo 'Hello World'",
    label="my-task",                    # 任務標籤
    working_directory="/tmp",           # 工作目錄
    group="my-group",                   # 指定組
    priority=10,                        # 優先級（數字越大優先級越高）
    after=[1, 2],                       # 依賴任務 ID 列表
    delay="5m",                         # 延遲執行（5分鐘後）
    immediate=True,                     # 立即執行
    follow=True,                        # 跟隨輸出
    stashed=False,                      # 是否暫存
    escape=False,                       # 轉義特殊字符
    print_task_id=True                  # 返回任務 ID
)
```

### 2. Group 管理功能

完整的 group 管理 API：

```python
# 獲取所有組
groups = await pueue.get_groups()

# 創建新組
result = await pueue.add_group("new-group")

# 刪除組
result = await pueue.remove_group("old-group")

# 設置組的並行任務數
result = await pueue.set_group_parallel(5, "my-group")
```

### 3. 任務控制功能

全面的任務控制操作：

```python
# 移除任務
result = await pueue.remove_task([1, 2, 3])

# 殺死運行中的任務
result = await pueue.kill_task([1, 2])

# 暫停任務或組
result = await pueue.pause_task([1, 2])
result = await pueue.pause_task([], group="my-group")

# 啟動/恢復任務或組
result = await pueue.start_task([1, 2])
result = await pueue.start_task([], group="my-group")

# 重啟任務
result = await pueue.restart_task([1, 2], in_place=True)

# 清理已完成的任務
result = await pueue.clean_tasks("my-group")

# 重置隊列（移除所有任務）
result = await pueue.reset_queue("my-group")
```

### 4. 新的 Pydantic 模型

添加了新的數據模型來支持新功能：

- `GroupStatus`: 組狀態枚舉
- `TaskAddOptions`: 添加任務的選項
- `TaskControl`: 任務控制操作的結果

### 5. 同步包裝器更新

`PueueWrapperSync` 同步包裝器現在支持所有新功能，提供完整的同步 API。

### 6. FastAPI 接口更新

完整的 REST API 接口：

#### 增強的任務添加
```
GET /api/add?command=echo hello&group=my-group&working_directory=/tmp&priority=10
```

#### Group 管理
```
GET /api/groups                      # 獲取所有組
POST /api/groups/{group_name}        # 創建組
DELETE /api/groups/{group_name}      # 刪除組
PUT /api/groups/{group_name}/parallel?parallel_tasks=5  # 設置並行數
```

#### 任務控制
```
DELETE /api/tasks?task_ids=1,2,3     # 移除任務
POST /api/tasks/kill?task_ids=1,2    # 殺死任務
POST /api/tasks/pause?group=my-group # 暫停組
POST /api/tasks/start?task_ids=1,2   # 啟動任務
POST /api/tasks/restart?task_ids=1,2 # 重啟任務
DELETE /api/tasks/clean?group=my-group # 清理任務
DELETE /api/tasks/reset              # 重置隊列
```

## 使用示例

請參考以下示例文件：
- `examples/example_new_features.py` - 新功能的完整演示
- `examples/example_status.py` - 狀態查詢示例
- `examples/example_usage.py` - 基本用法示例

## 主要改進

1. **完整的 CLI 支持**: 現在支持幾乎所有 Pueue CLI 的功能
2. **工作目錄支持**: 可以為任務指定執行目錄
3. **組管理**: 完整的組創建、刪除、配置功能
4. **任務依賴**: 支持任務間的依賴關係
5. **優先級控制**: 支持任務優先級設置
6. **延遲執行**: 支持定時和延遲任務
7. **批量操作**: 支持批量任務控制
8. **同步和異步**: 提供完整的同步和異步 API
9. **REST API**: 完整的 HTTP REST 接口
10. **類型安全**: 使用 Pydantic 模型確保類型安全

## 兼容性

所有新功能都保持向後兼容性，現有代碼無需修改即可使用。

## 測試

運行新功能示例：

```bash
# 測試異步功能
python examples/example_new_features.py

# 啟動 API 服務器
python api.py
# 訪問 http://localhost:8000/docs 查看 API 文檔
```
