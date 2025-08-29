#!/usr/bin/env python3
"""
PueueWrapper Streamlit UI Server CLI

使用 Tyro 來創建命令行介面，啟動 Streamlit UI 服務器
"""

import tyro
import subprocess
import sys
from pathlib import Path
from typing import Optional


def main(
    port: int = 8501,
    # host: str = "0.0.0.0",
    browser: bool = True,
    server_headless: bool = False,
    theme_base: str = "light",
    server_max_upload_size: int = 200,
) -> None:
    """
    啟動 PueueWrapper Streamlit UI 服務器

    Args:
        port: Streamlit 服務器端口
        host: 服務器綁定的主機地址
        browser: 是否自動打開瀏覽器
        server_headless: 是否以無頭模式運行（無瀏覽器）
        theme_base: UI 主題 (light, dark)
        server_max_upload_size: 最大上傳文件大小 (MB)
    """

    # 獲取當前文件所在目錄
    ui_dir = Path(__file__).parent
    overview_file = ui_dir / "Overview.py"

    if not overview_file.exists():
        print("❌ 錯誤: 找不到 Overview.py 文件")
        print(f"📁 請確保文件位於: {overview_file}")
        sys.exit(1)

    # 構建 streamlit 命令
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(overview_file),
        "--server.port",
        str(port),
        # "--server.address",
        # host,
        "--theme.base",
        theme_base,
        "--server.maxUploadSize",
        str(server_max_upload_size),
    ]

    # 添加可選參數
    if not browser:
        cmd.extend(["--browser.gatherUsageStats", "false"])

    if server_headless:
        cmd.extend(["--server.headless", "true"])
    else:
        cmd.extend(["--server.headless", "false"])

    print(f"🚀 正在啟動 PueueWrapper Streamlit UI...")
    # print(f"📍 地址: http://{host}:{port}")
    print(f"📍 地址: http://localhost:{port}")
    print(f"🎨 主題: {theme_base}")
    print(f"📁 UI 目錄: {ui_dir}")
    if browser and not server_headless:
        print(f"🌐 瀏覽器將自動打開")
    print("-" * 50)

    # 檢查依賴
    try:
        import streamlit
        import plotly

        print(f"✅ Streamlit 版本: {streamlit.__version__}")
        print(f"✅ Plotly 版本: {plotly.__version__}")
    except ImportError as e:
        print(f"❌ 依賴檢查失敗: {e}")
        print("💡 請安裝 UI 依賴: uv sync --group ui")
        sys.exit(1)

    # 啟動 Streamlit
    try:
        subprocess.run(cmd, cwd=ui_dir, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ 啟動 Streamlit 失敗: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 服務器已停止")


def cli() -> None:
    """CLI entry point for the pueue-ui-server command."""
    tyro.cli(main)


if __name__ == "__main__":
    cli()
