"""
任務模板頁面

管理和使用常用的任務模板
"""

import streamlit as st
import json
from datetime import datetime
from typing import Dict, List, Optional
from pathlib import Path

# Import shared components
import sys

sys.path.append(str(Path(__file__).parent.parent))

from shared_components import (
    init_session_state,
    setup_sidebar_config,
    async_runner,
    refresh_button,
    show_last_refresh,
    display_error,
    display_success,
    add_submitted_task,
)


# 預定義的模板
DEFAULT_TEMPLATES = {
    "系統監控": {
        "command": "top -n 1",
        "label": "system_monitor",
        "group": "monitoring",
        "description": "查看系統資源使用情況",
    },
    "磁盤使用": {
        "command": "df -h",
        "label": "disk_usage",
        "group": "monitoring",
        "description": "檢查磁盤使用情況",
    },
    "Python 腳本": {
        "command": "python script.py",
        "label": "python_task",
        "group": "development",
        "description": "執行 Python 腳本",
    },
    "Git 同步": {
        "command": "git pull origin main",
        "label": "git_sync",
        "group": "development",
        "description": "同步 Git 倉庫",
    },
    "數據備份": {
        "command": "rsync -av /source/ /backup/",
        "label": "data_backup",
        "group": "maintenance",
        "description": "使用 rsync 備份數據",
    },
    "日誌清理": {
        "command": "find /var/log -name '*.log' -mtime +7 -delete",
        "label": "log_cleanup",
        "group": "maintenance",
        "description": "清理 7 天前的日誌文件",
    },
}


def main():
    """任務模板主頁面"""
    st.set_page_config(
        page_title="PueueWrapper UI - 任務模板", page_icon="📝", layout="wide"
    )

    # 初始化
    init_session_state()

    # 標題
    st.title("📝 任務模板")
    st.markdown("---")

    # 側邊欄配置
    config = setup_sidebar_config()

    # 初始化模板存儲
    _init_templates()

    # 主要內容區域
    tab1, tab2, tab3 = st.tabs(["📋 使用模板", "➕ 創建模板", "🔧 管理模板"])

    with tab1:
        _display_template_usage(config)

    with tab2:
        _display_template_creation()

    with tab3:
        _display_template_management()


def _init_templates():
    """初始化模板存儲"""
    if "task_templates" not in st.session_state:
        st.session_state.task_templates = DEFAULT_TEMPLATES.copy()


def _display_template_usage(config):
    """顯示模板使用界面"""
    st.subheader("📋 使用任務模板")

    templates = st.session_state.task_templates

    if not templates:
        st.info("沒有可用的模板，請先創建一些模板")
        return

    # 模板選擇
    template_names = list(templates.keys())
    selected_template = st.selectbox(
        "選擇模板",
        options=template_names,
        format_func=lambda x: f"{x} - {templates[x].get('description', '無描述')}",
    )

    if selected_template:
        template = templates[selected_template]

        # 顯示模板信息
        st.subheader(f"🎯 模板: {selected_template}")

        col1, col2 = st.columns(2)

        with col1:
            st.write(f"**描述:** {template.get('description', '無描述')}")
            st.write(f"**默認組:** {template.get('group', 'default')}")
            st.write(f"**默認標籤:** {template.get('label', '無')}")

        with col2:
            st.write(f"**優先級:** {template.get('priority', 0)}")
            st.write(f"**工作目錄:** {template.get('working_dir', '當前目錄')}")

        # 命令預覽
        st.write("**命令:**")
        st.code(template["command"], language="bash")

        # 自定義參數
        st.subheader("⚙️ 自定義參數")

        # 允許修改模板參數
        col1, col2 = st.columns(2)

        with col1:
            custom_command = st.text_area(
                "命令（可修改）", value=template["command"], height=100
            )

            custom_label = st.text_input(
                "標籤（可修改）", value=template.get("label", "")
            )

        with col2:
            custom_group = st.text_input(
                "組（可修改）", value=template.get("group", config["default_group"])
            )

            custom_priority = st.number_input(
                "優先級（可修改）",
                value=template.get("priority", config["priority"]),
                min_value=-100,
                max_value=100,
            )

        custom_working_dir = st.text_input(
            "工作目錄（可修改）",
            value=template.get("working_dir", config["working_dir"]),
        )

        # 提交按鈕
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("🚀 提交任務", type="primary", use_container_width=True):
                _submit_template_task(
                    custom_command,
                    custom_label,
                    custom_working_dir,
                    custom_group,
                    custom_priority,
                    config,
                )

        with col2:
            if st.button("⏳ 提交並等待", use_container_width=True):
                _submit_and_wait_template_task(
                    custom_command,
                    custom_label,
                    custom_working_dir,
                    custom_group,
                    custom_priority,
                    config,
                )

        with col3:
            if st.button("💾 保存為新模板", use_container_width=True):
                _save_as_new_template(
                    custom_command,
                    custom_label,
                    custom_group,
                    custom_priority,
                    custom_working_dir,
                )


def _display_template_creation():
    """顯示模板創建界面"""
    st.subheader("➕ 創建新模板")

    with st.form("create_template_form"):
        col1, col2 = st.columns(2)

        with col1:
            template_name = st.text_input("模板名稱 *", placeholder="例如: 數據處理")

            template_description = st.text_area(
                "模板描述", placeholder="描述這個模板的用途...", height=80
            )

            template_group = st.text_input(
                "默認組", value="default", placeholder="default"
            )

        with col2:
            template_label = st.text_input(
                "默認標籤", placeholder="例如: data_processing"
            )

            template_priority = st.number_input(
                "默認優先級", value=0, min_value=-100, max_value=100
            )

            template_working_dir = st.text_input(
                "默認工作目錄", placeholder="留空使用當前目錄"
            )

        template_command = st.text_area(
            "命令模板 *",
            placeholder="例如: python process_data.py --input {input_file} --output {output_file}",
            height=120,
            help="可以使用 {變量名} 作為佔位符",
        )

        # 參數定義
        st.write("**參數定義（可選）:**")
        template_params = st.text_area(
            "參數說明",
            placeholder="input_file: 輸入文件路徑\noutput_file: 輸出文件路徑",
            height=60,
            help="每行一個參數說明，格式: 參數名: 說明",
        )

        submitted = st.form_submit_button("💾 創建模板", type="primary")

        if submitted:
            if template_name.strip() and template_command.strip():
                _create_template(
                    template_name.strip(),
                    template_command.strip(),
                    template_description.strip(),
                    template_group.strip() or "default",
                    template_label.strip(),
                    template_priority,
                    template_working_dir.strip(),
                    template_params.strip(),
                )
            else:
                st.error("請填寫模板名稱和命令")


def _display_template_management():
    """顯示模板管理界面"""
    st.subheader("🔧 模板管理")

    templates = st.session_state.task_templates

    if not templates:
        st.info("沒有可用的模板")
        return

    # 模板列表
    st.write("**現有模板:**")

    for name, template in templates.items():
        with st.expander(f"📝 {name}"):
            col1, col2, col3 = st.columns([3, 1, 1])

            with col1:
                st.write(f"**描述:** {template.get('description', '無描述')}")
                st.write(f"**組:** {template.get('group', 'default')}")
                st.write(f"**標籤:** {template.get('label', '無')}")
                st.code(template["command"], language="bash")

                if template.get("params"):
                    st.write("**參數說明:**")
                    st.text(template["params"])

            with col2:
                if st.button("📝 編輯", key=f"edit_{name}"):
                    _edit_template(name)

            with col3:
                if st.button("🗑️ 刪除", key=f"delete_{name}"):
                    _delete_template(name)

    # 導入/導出功能
    st.markdown("---")
    st.subheader("📁 導入/導出模板")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**導出模板:**")
        if st.button("📤 導出所有模板"):
            _export_templates()

    with col2:
        st.write("**導入模板:**")
        uploaded_file = st.file_uploader(
            "選擇模板文件", type=["json"], help="上傳之前導出的模板文件"
        )

        if uploaded_file is not None:
            if st.button("📥 導入模板"):
                _import_templates(uploaded_file)


def _submit_template_task(command, label, working_dir, group, priority, config):
    """提交模板任務"""
    try:
        wrapper = st.session_state.pueue_wrapper

        task_id = async_runner.run(
            wrapper.add_task(
                command=command,
                label=label or None,
                working_directory=(
                    working_dir if working_dir != config["working_dir"] else None
                ),
                group=group if group != "default" else None,
                priority=priority if priority != 0 else None,
            )
        )

        if task_id:
            display_success(f"任務已成功提交！任務 ID: {task_id}")
            add_submitted_task(task_id, command, label)
            st.rerun()
        else:
            st.error("提交任務失敗")

    except Exception as e:
        display_error(e)


def _submit_and_wait_template_task(
    command, label, working_dir, group, priority, config
):
    """提交模板任務並等待"""
    try:
        wrapper = st.session_state.pueue_wrapper

        with st.spinner("正在提交任務並等待完成..."):
            result = async_runner.run(
                wrapper.submit_and_wait_and_get_output(command, label)
            )

            if result is not None:
                display_success("任務完成！輸出如下：")
                st.subheader("📄 任務輸出")
                st.code(result, language="bash")
            else:
                st.error("獲取任務輸出失敗")

    except Exception as e:
        display_error(e)


def _save_as_new_template(command, label, group, priority, working_dir):
    """保存為新模板"""
    template_name = st.text_input("新模板名稱", key="save_template_name")
    template_desc = st.text_input("模板描述", key="save_template_desc")

    if st.button("💾 保存", key="save_template_btn"):
        if template_name.strip():
            _create_template(
                template_name.strip(),
                command,
                template_desc.strip(),
                group,
                label,
                priority,
                working_dir,
                "",
            )
        else:
            st.error("請輸入模板名稱")


def _create_template(
    name, command, description, group, label, priority, working_dir, params
):
    """創建新模板"""
    templates = st.session_state.task_templates

    if name in templates:
        st.error(f"模板 '{name}' 已存在")
        return

    templates[name] = {
        "command": command,
        "description": description,
        "group": group,
        "label": label,
        "priority": priority,
        "working_dir": working_dir,
        "params": params,
        "created_at": datetime.now().isoformat(),
    }

    st.session_state.task_templates = templates
    display_success(f"模板 '{name}' 創建成功！")
    st.rerun()


def _edit_template(name):
    """編輯模板"""
    templates = st.session_state.task_templates
    template = templates[name]

    st.subheader(f"📝 編輯模板: {name}")

    with st.form(f"edit_template_{name}"):
        new_command = st.text_area("命令", value=template["command"], height=100)
        new_description = st.text_area("描述", value=template.get("description", ""))
        new_group = st.text_input("組", value=template.get("group", "default"))
        new_label = st.text_input("標籤", value=template.get("label", ""))
        new_priority = st.number_input(
            "優先級", value=template.get("priority", 0), min_value=-100, max_value=100
        )
        new_working_dir = st.text_input(
            "工作目錄", value=template.get("working_dir", "")
        )
        new_params = st.text_area("參數說明", value=template.get("params", ""))

        if st.form_submit_button("💾 保存修改"):
            templates[name] = {
                "command": new_command,
                "description": new_description,
                "group": new_group,
                "label": new_label,
                "priority": new_priority,
                "working_dir": new_working_dir,
                "params": new_params,
                "created_at": template.get("created_at"),
                "updated_at": datetime.now().isoformat(),
            }

            st.session_state.task_templates = templates
            display_success(f"模板 '{name}' 更新成功！")
            st.rerun()


def _delete_template(name):
    """刪除模板"""
    templates = st.session_state.task_templates

    st.warning(f"⚠️ 確認要刪除模板 '{name}' 嗎？")

    col1, col2 = st.columns(2)

    with col1:
        if st.button("✅ 確認刪除", key=f"confirm_delete_{name}"):
            del templates[name]
            st.session_state.task_templates = templates
            display_success(f"模板 '{name}' 已刪除")
            st.rerun()

    with col2:
        if st.button("❌ 取消", key=f"cancel_delete_{name}"):
            st.rerun()


def _export_templates():
    """導出模板"""
    templates = st.session_state.task_templates

    if templates:
        export_data = {
            "templates": templates,
            "export_date": datetime.now().isoformat(),
            "version": "1.0",
        }

        json_str = json.dumps(export_data, indent=2, ensure_ascii=False)

        st.download_button(
            label="📥 下載模板文件",
            data=json_str,
            file_name=f"pueue_templates_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            mime="application/json",
        )
    else:
        st.warning("沒有模板可導出")


def _import_templates(uploaded_file):
    """導入模板"""
    try:
        import_data = json.load(uploaded_file)

        if "templates" in import_data:
            imported_templates = import_data["templates"]
            current_templates = st.session_state.task_templates

            # 檢查衝突
            conflicts = []
            for name in imported_templates:
                if name in current_templates:
                    conflicts.append(name)

            if conflicts:
                st.warning(f"以下模板已存在，將會被覆蓋: {', '.join(conflicts)}")

                if st.button("確認導入並覆蓋"):
                    current_templates.update(imported_templates)
                    st.session_state.task_templates = current_templates
                    display_success(f"成功導入 {len(imported_templates)} 個模板")
                    st.rerun()
            else:
                current_templates.update(imported_templates)
                st.session_state.task_templates = current_templates
                display_success(f"成功導入 {len(imported_templates)} 個模板")
                st.rerun()
        else:
            st.error("無效的模板文件格式")

    except json.JSONDecodeError:
        st.error("無法解析 JSON 文件")
    except Exception as e:
        display_error(e)


if __name__ == "__main__":
    main()
