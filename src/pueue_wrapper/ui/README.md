# PueueWrapper Streamlit UI

一個基於 Streamlit 的 Web 界面，用於管理 Pueue 任務隊列系統。

## 🚀 快速開始

### 1. 安裝依賴

```bash
# 安裝 UI 相關依賴
uv sync --group ui

# 或者手動安裝
pip install streamlit plotly pandas
```

### 2. 確保 Pueue 運行

```bash
# 安裝 Pueue (如果尚未安裝)
cargo install pueue

# 啟動 Pueue 守護進程
pueued
```

### 3. 啟動 UI 服務器

```bash
# 使用項目腳本啟動
pueue-ui-server

# 或者直接使用 Streamlit
streamlit run Overview.py

# 自定義端口和主機
pueue-ui-server --port 8502 --host localhost
```

## 📱 功能特性

### 核心功能
- **📊 概覽頁面**: 系統狀態總覽和統計圖表
- **📝 提交任務**: 單個/批量任務提交，支持所有 Pueue 參數
- **📋 任務狀態**: 實時任務列表，支持篩選和批量操作
- **🔧 任務管理**: 高級任務控制和批量操作
- **📜 日誌查看**: 任務日誌瀏覽和下載
- **👥 組管理**: 任務組創建、配置和管理

### 擴展功能
- **📝 任務模板**: 常用任務模板管理
- **❓ 使用幫助**: 詳細的使用說明和FAQ

### 提交模式
1. **異步提交**: 立即返回，任務在後台執行
2. **同步等待**: 等待任務完成並顯示結果
3. **獲取輸出**: 等待完成並顯示任務輸出

## 🏗️ 頁面結構

```
ui/
├── Overview.py              # 主頁概覽
├── shared_components.py     # 共享組件和工具
├── run_ui_server.py        # 服務器啟動腳本
├── pages/
│   ├── Submit_Task.py      # 任務提交
│   ├── Task_Status.py      # 任務狀態
│   ├── Task_Management.py  # 任務管理
│   ├── Logs.py            # 日誌查看
│   ├── Groups.py          # 組管理
│   ├── Task_Templates.py  # 任務模板
│   └── Help.py            # 使用幫助
└── README.md              # 本文件
```

## ⚙️ 配置選項

### 側邊欄配置
- **工作目錄**: 任務執行的默認目錄
- **默認組**: 新任務的默認組
- **優先級**: 任務默認優先級
- **自動刷新**: 界面自動刷新設置

### 高級選項
- **轉義特殊字符**: 自動轉義 shell 特殊字符
- **立即開始**: 添加任務後立即開始執行
- **打印任務 ID**: 顯示任務 ID

## 🔧 命令行選項

```bash
pueue-ui-server --help
```

可用選項：
- `--port`: 服務器端口 (默認: 8501)
- `--host`: 綁定主機 (默認: 0.0.0.0)
- `--browser`: 是否自動打開瀏覽器 (默認: true)
- `--server-headless`: 無頭模式運行 (默認: false)
- `--theme-base`: UI 主題 (light/dark, 默認: light)

## 📊 功能說明

### 任務管理
- 支持所有 Pueue 任務操作 (暫停、開始、重啟、刪除等)
- 批量操作多個任務
- 任務依賴關係設置
- 延遲執行和優先級控制

### 組管理
- 創建和刪除任務組
- 設置組並行執行數量
- 組級別的暫停和啟動
- 組統計和可視化

### 日誌功能
- 實時日誌查看
- 結構化和純文本兩種格式
- 日誌過濾和搜索
- 日誌下載功能

### 任務模板
- 預定義常用任務模板
- 自定義模板創建和編輯
- 模板導入/導出
- 參數化命令支持

## 🐛 故障排除

### 常見問題

1. **無法連接到 Pueue**
   - 確保 `pueued` 正在運行
   - 檢查權限設置

2. **UI 依賴錯誤**
   ```bash
   uv sync --group ui
   ```

3. **任務不顯示**
   - 檢查組篩選設置
   - 刷新頁面
   - 確認 Pueue 連接

4. **性能問題**
   - 關閉自動刷新
   - 清理已完成任務
   - 使用任務篩選

### 調試信息

檢查 Pueue 狀態：
```bash
pueue status
pueue log
```

檢查依賴：
```bash
python -c "import streamlit, plotly, pydantic; print('OK')"
```

## 📝 開發說明

### 技術棧
- **Streamlit**: Web UI 框架
- **Plotly**: 圖表可視化
- **Pandas**: 數據處理
- **Pydantic**: 數據驗證
- **PueueWrapper**: 異步 Pueue 包裝器

### 異步處理
所有 Pueue 操作都是異步的，使用 `async_runner` 在 Streamlit 中執行異步函數。

### 狀態管理
使用 Streamlit session state 管理：
- PueueWrapper 實例
- 已提交任務列表
- 任務模板
- 用戶配置

## 📄 許可證

本項目遵循與主項目相同的許可證。
