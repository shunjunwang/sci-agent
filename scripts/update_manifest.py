"""
文档清单自动更新脚本
扫描 D:\projects\sci-agent\docs\ 目录，自动更新 MANIFEST.yaml
用法：
  python update_manifest.py          # 扫描并更新
  python update_manifest.py --check  # 仅检查，不修改（报告哪些文档需要更新）
"""

import os
import yaml
import hashlib
from datetime import datetime, timezone, timedelta
from pathlib import Path

PROJECT_ROOT = Path(r"D:\projects\sci-agent")
DOCS_DIR = PROJECT_ROOT / "docs"
MANIFEST_PATH = PROJECT_ROOT / "docs" / "MANIFEST.yaml"
AI_CONTEXT_PATH = PROJECT_ROOT / "AI_CONTEXT.md"

# 扫描两个目录：项目根目录的 .md + docs/ 的 .md
SCAN_DIRS = [PROJECT_ROOT, DOCS_DIR]

# 已知文档的元数据模板（新文档自动发现时会用默认值）
KNOWN_DOCS = {
    "AI_CONTEXT.md": {
        "purpose": "AI 会话入口索引，技术栈摘要，文档索引，AI 行为准则",
        "category": "governance",
    },
    "SPEC.md": {
        "purpose": "API 契约（唯一真相源）：产品定义、9 模块规格、16 张数据表、统一规范、验收 checklist",
        "category": "core",
    },
    "ARCHITECTURE.md": {
        "purpose": "技术架构：18 项技术选型、6 条 ADR、系统架构图",
        "category": "core",
    },
    "AI_COLLABORATION.md": {
        "purpose": "AI 协同开发规范：5 条铁律、Task 格式标准、分支规范、10 条禁止事项",
        "category": "governance",
    },
    "UI_LAYOUT.md": {
        "purpose": "三栏界面布局规格：10 章完整布局、CSS 变量配色、响应式规则、组件树映射",
        "category": "design",
    },
    "TEST_STRATEGY.md": {
        "purpose": "测试策略：测试金字塔 70/25/5、AI 自动生成测试用例流程",
        "category": "governance",
    },
    "PROGRESS.md": {
        "purpose": "开发进度追踪：3 波里程碑、全部模块状态表、每日更新",
        "category": "tracking",
    },
    "RISK_MANAGEMENT.md": {
        "purpose": "风险登记册：7 项风险（含缓解、应急、触发条件）",
        "category": "governance",
    },
    "功能增强方案-对话管理_科研工具_加密格式.md": {
        "purpose": "增量功能方案：对话搜索/管理、科研绘图工具扩展、.scix 加密格式设计",
        "category": "feature",
    },
    "文档治理方案-AI多文档引用可靠性.md": {
        "purpose": "多文档环境下 AI 如何可靠引用最新版本的治理规范",
        "category": "governance",
    },
}

DEPENDENCY_CHAINS = [
    {
        "chain": ["SPEC.md", "ARCHITECTURE.md", "TEST_STRATEGY.md"],
        "rule": "SPEC 变更 → 检查架构和测试策略是否需要同步调整",
    },
    {
        "chain": ["SPEC.md", "UI_LAYOUT.md", "功能增强方案-对话管理_科研工具_加密格式.md"],
        "rule": "SPEC 或 UI 变更 → 检查功能增量方案是否受影响",
    },
    {
        "chain": ["SPEC.md", "PROGRESS.md"],
        "rule": "模块 API 定义变更 → 更新进度表中对应模块状态",
    },
    {
        "chain": ["AI_CONTEXT.md", "MANIFEST.yaml"],
        "rule": "任何新文档注册或删除 → 同步更新 AI_CONTEXT.md 的文档索引",
    },
]


def get_file_info(filepath: Path, existing: dict | None = None) -> dict:
    """获取文件信息，与已有条目合并"""
    stat = filepath.stat()
    mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone(timedelta(hours=8)))
    mtime_str = mtime.strftime("%Y-%m-%d")

    name = filepath.name
    known = KNOWN_DOCS.get(name, {})

    # 如果已有条目且修改时间没变，版本号不变
    if existing and existing.get("last_modified") == mtime_str:
        return existing

    # 修改时间变了 → 版本号 +0.1
    new_version = "1.0"
    if existing:
        try:
            old_ver = float(existing.get("version", "1.0"))
            new_version = f"{old_ver + 0.1:.1f}"
        except ValueError:
            pass

    return {
        "purpose": known.get("purpose", f"待补充：{name} 的用途描述"),
        "version": new_version,
        "last_modified": mtime_str,
        "dependencies": existing.get("dependencies", []) if existing else [],
        "category": known.get("category", "uncategorized"),
    }


def scan_and_update(check_only: bool = False) -> dict:
    """扫描文档目录，生成或检查 MANIFEST.yaml"""
    changes = {"new": [], "updated": [], "removed": [], "unchanged": 0}

    # 读取现有 MANIFEST
    existing_docs = {}
    manifest_data = {}
    if MANIFEST_PATH.exists():
        with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
            manifest_data = yaml.safe_load(f) or {}
        existing_docs = manifest_data.get("documents", {})

    # 扫描项目根目录和 docs/ 下的 .md 文件
    current_files = {}
    for scan_dir in SCAN_DIRS:
        for f in scan_dir.glob("*.md"):
            # 跳过 MANIFEST.yaml 和 session-log.md（它们不是被管理的文档）
            if f.name in ("MANIFEST.md",):
                continue
            existing = existing_docs.get(f.name)
            current_files[f.name] = get_file_info(f, existing)

            if f.name not in existing_docs:
                changes["new"].append(f.name)
            elif current_files[f.name]["last_modified"] != existing.get("last_modified"):
                changes["updated"].append(f.name)
            else:
                changes["unchanged"] += 1

    # 检查已删除的文档
    for name in existing_docs:
        if name not in current_files:
            changes["removed"].append(name)

    if check_only:
        return changes

    # 写入新 MANIFEST
    new_manifest = {
        "manifest_version": "1.0",
        "last_updated": datetime.now(timezone(timedelta(hours=8))).strftime(
            "%Y-%m-%dT%H:%M:%S+08:00"
        ),
        "total_documents": len(current_files),
        "documents": current_files,
        "dependency_chains": DEPENDENCY_CHAINS,
    }

    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        yaml.dump(new_manifest, f, allow_unicode=True, default_flow_style=False, sort_keys=False)

    return changes


if __name__ == "__main__":
    import sys

    check_only = "--check" in sys.argv
    changes = scan_and_update(check_only)

    if check_only:
        print("=== 文档变更检查 ===")
        if changes["new"]:
            print(f"新增文档 ({len(changes['new'])}): {', '.join(changes['new'])}")
        if changes["updated"]:
            print(f"已修改文档 ({len(changes['updated'])}): {', '.join(changes['updated'])}")
        if changes["removed"]:
            print(f"已删除文档 ({len(changes['removed'])}): {', '.join(changes['removed'])}")
        if changes["unchanged"]:
            print(f"未变化文档: {changes['unchanged']} 个")
        if not any([changes["new"], changes["updated"], changes["removed"]]):
            print("所有文档均无变化。")
    else:
        print("MANIFEST.yaml 已更新。")
        if changes["new"]:
            print(f"  新增: {', '.join(changes['new'])}")
        if changes["updated"]:
            print(f"  更新: {', '.join(changes['updated'])}")
        if changes["removed"]:
            print(f"  移除: {', '.join(changes['removed'])}")
        print(f"  文档总数: {len(changes['unchanged']) + len(changes['new']) + len(changes['updated'])}")
