#!/usr/bin/env python3
"""
PueueWrapper API Server CLI

使用 Tyro 來創建命令行介面，啟動 FastAPI 服務器
"""

import tyro
from typing import Optional
import uvicorn
from pathlib import Path


def main(
    host: str = "0.0.0.0",
    port: int = 8000,
    reload: bool = False,
    workers: Optional[int] = None,
    log_level: str = "info",
) -> None:
    """
    啟動 PueueWrapper API 服務器

    Args:
        host: 服務器綁定的主機地址
        port: 服務器端口
        reload: 開發模式下自動重載 (與 workers 互斥)
        workers: 工作程序數量 (生產環境建議設置，與 reload 互斥)
        log_level: 日誌級別 (debug, info, warning, error, critical)
    """

    # 驗證參數
    if reload and workers and workers > 1:
        print("警告: reload 模式與多個 workers 不相容，將使用 reload 模式")
        workers = None

    # 構建 app 模組路徑
    app_module = "pueue_wrapper.api.api:app"

    print(f"🚀 正在啟動 PueueWrapper API 服務器...")
    print(f"📍 地址: http://{host}:{port}")
    print(f"📖 API 文檔: http://{host}:{port}/docs")
    print(f"🔧 重載模式: {'開啟' if reload else '關閉'}")
    if workers:
        print(f"👷 工作程序數: {workers}")
    print(f"📊 日誌級別: {log_level}")
    print("-" * 50)

    # 啟動服務器
    uvicorn.run(
        app_module,
        host=host,
        port=port,
        reload=reload,
        workers=workers,
        log_level=log_level,
    )


def cli() -> None:
    """CLI entry point for the pueue-api-server command."""
    tyro.cli(main)


if __name__ == "__main__":
    cli()
