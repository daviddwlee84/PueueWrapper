"""
幫助頁面

提供 PueueWrapper UI 的使用說明和常見問題解答
"""

import streamlit as st

# Import shared components
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from shared_components import init_session_state, setup_sidebar_config


def main():
    """幫助頁面"""
    st.set_page_config(
        page_title="PueueWrapper UI - 幫助", page_icon="❓", layout="wide"
    )

    # 初始化
    init_session_state()

    # 標題
    st.title("❓ 使用幫助")
    st.markdown("---")

    # 主要內容區域
    tab1, tab2, tab3, tab4 = st.tabs(
        ["📖 快速開始", "📋 功能介紹", "❓ 常見問題", "🔧 技術說明"]
    )

    with tab1:
        _display_quick_start()

    with tab2:
        _display_features()

    with tab3:
        _display_faq()

    with tab4:
        _display_technical_info()


def _display_quick_start():
    """顯示快速開始指南"""
    st.subheader("📖 快速開始")

    st.markdown(
        """
    ## 歡迎使用 PueueWrapper UI！
    
    這是一個基於 Streamlit 的 Web 界面，用於管理 Pueue 任務隊列系統。
    
    ### 🚀 第一次使用
    
    1. **確保 Pueue 已安裝並運行**
       ```bash
       # 安裝 Pueue
       cargo install pueue
       
       # 啟動 Pueue 守護進程
       pueued
       ```
    
    2. **確保 PueueWrapper 依賴已安裝**
       ```bash
       # 安裝 UI 依賴
       uv sync --group ui
       ```
    
    3. **啟動 UI 服務器**
       ```bash
       # 使用命令行工具啟動
       pueue-ui-server
       
       # 或者直接運行
       streamlit run ui/Overview.py
       ```
    
    ### 📱 界面導航
    
    - **概覽頁面**: 查看系統整體狀態和統計信息
    - **提交任務**: 提交新的任務到隊列
    - **任務狀態**: 查看和管理現有任務
    - **任務管理**: 執行批量操作和高級管理
    - **查看日誌**: 查看任務執行日誌和輸出
    - **組管理**: 管理任務組和並行設置
    - **任務模板**: 創建和使用常用任務模板
    
    ### ⚡ 快速操作
    
    在每個頁面的側邊欄中，您可以設置：
    - 工作目錄
    - 默認組
    - 任務優先級
    - 自動刷新設置
    """
    )


def _display_features():
    """顯示功能介紹"""
    st.subheader("📋 功能介紹")

    # 概覽頁面
    with st.expander("📊 概覽頁面"):
        st.markdown(
            """
        **主要功能:**
        - 系統狀態總覽（總任務數、運行中、排隊中、已完成、失敗）
        - 組狀態顯示
        - 最近任務列表
        - 任務狀態分佈圖表
        - 快速操作面板
        
        **使用場景:**
        - 快速了解系統整體狀況
        - 監控任務執行進度
        - 快速跳轉到其他功能頁面
        """
        )

    # 提交任務
    with st.expander("📝 提交任務"):
        st.markdown(
            """
        **主要功能:**
        - 單個任務提交（支持所有 Pueue 參數）
        - 批量任務提交
        - 三種提交模式：
          - 異步提交：立即返回任務 ID
          - 提交並等待：等待任務完成
          - 提交並獲取輸出：等待並顯示結果
        - 任務進度追蹤
        
        **高級選項:**
        - 工作目錄設置
        - 組和優先級
        - 依賴任務設置
        - 延遲執行
        - 立即開始、暫存狀態等
        """
        )

    # 任務狀態
    with st.expander("📋 任務狀態"):
        st.markdown(
            """
        **主要功能:**
        - 所有任務列表顯示
        - 按組和狀態篩選
        - 多選操作（暫停、開始、重啟、刪除）
        - 任務詳細信息查看
        - 實時狀態更新
        
        **表格功能:**
        - 排序和搜索
        - 列寬調整
        - 多行選擇
        """
        )

    # 任務管理
    with st.expander("🔧 任務管理"):
        st.markdown(
            """
        **主要功能:**
        - 單個任務精確控制
        - 批量操作界面
        - 並行任務設置
        - 清理和重置功能
        
        **安全機制:**
        - 危險操作確認
        - 狀態檢查
        - 錯誤處理
        """
        )

    # 日誌查看
    with st.expander("📜 查看日誌"):
        st.markdown(
            """
        **主要功能:**
        - 所有任務日誌瀏覽
        - 單個任務日誌查看
        - 結構化和純文本兩種格式
        - 日誌下載功能
        - 自動刷新
        
        **篩選功能:**
        - 按組篩選
        - 只顯示已完成任務
        - 日誌長度限制
        """
        )

    # 組管理
    with st.expander("👥 組管理"):
        st.markdown(
            """
        **主要功能:**
        - 組狀態概覽和統計
        - 創建新組
        - 修改並行槽位數
        - 組控制（暫停/啟動）
        - 組刪除（除默認組外）
        
        **統計圖表:**
        - 任務狀態分佈
        - 成功率對比
        - 實時數據更新
        """
        )

    # 任務模板
    with st.expander("📝 任務模板"):
        st.markdown(
            """
        **主要功能:**
        - 預定義任務模板
        - 自定義模板創建
        - 模板編輯和刪除
        - 參數化命令支持
        - 導入/導出功能
        
        **內置模板:**
        - 系統監控
        - 磁盤使用檢查
        - Python 腳本執行
        - Git 同步
        - 數據備份
        - 日誌清理
        """
        )


def _display_faq():
    """顯示常見問題"""
    st.subheader("❓ 常見問題")

    with st.expander("🔧 安裝和配置問題"):
        st.markdown(
            """
        **Q: 如何安裝 Pueue？**
        
        A: 使用 Cargo 安裝：
        ```bash
        cargo install pueue
        ```
        
        或者從 [GitHub Releases](https://github.com/Nukesor/pueue/releases) 下載預編譯版本。
        
        **Q: Pueue 守護進程沒有運行怎麼辦？**
        
        A: 在終端中運行：
        ```bash
        pueued
        ```
        
        **Q: UI 依賴安裝失敗？**
        
        A: 確保使用正確的命令：
        ```bash
        uv sync --group ui
        ```
        
        **Q: 無法連接到 Pueue？**
        
        A: 檢查：
        - Pueue 守護進程是否運行 (`pueue status`)
        - 權限設置是否正確
        - 配置文件路徑是否正確
        """
        )

    with st.expander("📱 使用問題"):
        st.markdown(
            """
        **Q: 為什麼我的任務沒有顯示？**
        
        A: 可能的原因：
        - 任務在不同的組中，檢查組篩選
        - 刷新頁面獲取最新狀態
        - 檢查 Pueue 連接狀態
        
        **Q: 任務卡在排隊狀態？**
        
        A: 檢查：
        - 組的並行槽位是否已滿
        - 是否有依賴任務未完成
        - 組是否被暫停
        
        **Q: 如何設置任務依賴？**
        
        A: 在提交任務時，在"依賴任務ID"欄位中輸入用逗號分隔的任務ID，例如：1,2,3
        
        **Q: 批量操作不起作用？**
        
        A: 確保：
        - 已選中要操作的任務
        - 任務狀態允許該操作
        - 有足夠的權限
        """
        )

    with st.expander("⚡ 性能問題"):
        st.markdown(
            """
        **Q: UI 響應很慢？**
        
        A: 嘗試：
        - 關閉自動刷新
        - 減少顯示的任務數量
        - 清理已完成的任務
        - 使用任務篩選
        
        **Q: 大量任務時如何優化？**
        
        A: 建議：
        - 定期清理已完成任務
        - 使用不同組分類任務
        - 適當設置並行槽位數
        - 使用批量操作
        """
        )


def _display_technical_info():
    """顯示技術說明"""
    st.subheader("🔧 技術說明")

    with st.expander("🏗️ 架構說明"):
        st.markdown(
            """
        **組件架構:**
        
        ```
        Streamlit UI
            ↓
        PueueWrapper (異步)
            ↓
        Pueue CLI
            ↓
        Pueue Daemon
        ```
        
        **核心組件:**
        - **Streamlit**: Web UI 框架
        - **PueueWrapper**: Python 異步包裝器
        - **Pueue**: 命令行任務隊列工具
        - **Plotly**: 圖表可視化
        - **Pandas**: 數據處理
        """
        )

    with st.expander("🔄 異步處理"):
        st.markdown(
            """
        **異步設計:**
        
        UI 使用異步設計來避免阻塞用戶界面：
        
        1. 所有 Pueue 操作都是異步的
        2. 使用 `async_runner` 在 Streamlit 中執行異步函數
        3. 長時間運行的操作顯示進度指示器
        
        **注意事項:**
        - 某些操作可能需要幾秒鐘完成
        - 網絡延遲可能影響響應速度
        - 大量任務時操作會較慢
        """
        )

    with st.expander("💾 數據存儲"):
        st.markdown(
            """
        **Session State:**
        
        UI 使用 Streamlit session state 存儲：
        - PueueWrapper 實例
        - 已提交任務列表
        - 任務模板
        - 用戶設置
        
        **持久化:**
        - 任務模板可以導出/導入
        - 其他數據在會話間不保留
        - 實際任務數據存儲在 Pueue 中
        """
        )

    with st.expander("🔐 安全考慮"):
        st.markdown(
            """
        **安全機制:**
        
        1. **命令執行**: 所有命令通過 Pueue 執行，繼承其安全模型
        2. **權限檢查**: 依賴 Pueue 的權限系統
        3. **輸入驗證**: 對用戶輸入進行基本驗證
        4. **危險操作**: 重要操作需要確認
        
        **注意事項:**
        - 用戶可以執行任意命令
        - 建議在受控環境中使用
        - 注意文件權限和路徑安全
        """
        )

    with st.expander("🐛 故障排除"):
        st.markdown(
            """
        **調試步驟:**
        
        1. **檢查 Pueue 狀態:**
           ```bash
           pueue status
           ```
        
        2. **查看 Pueue 日誌:**
           ```bash
           pueue log
           ```
        
        3. **重啟 UI:**
           ```bash
           # 停止當前 UI (Ctrl+C)
           # 重新啟動
           pueue-ui-server
           ```
        
        4. **檢查依賴:**
           ```bash
           python -c "import streamlit, plotly, pydantic; print('Dependencies OK')"
           ```
        
        **常見錯誤:**
        - `ConnectionError`: Pueue 守護進程未運行
        - `ImportError`: 缺少依賴包
        - `PermissionError`: 權限不足
        - `FileNotFoundError`: 路徑不存在
        """
        )


if __name__ == "__main__":
    main()
