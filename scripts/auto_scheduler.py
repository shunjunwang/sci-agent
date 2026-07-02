"""
项目自动化调度器 — 定期执行任务的统一入口
==============================================
支持三种执行模式：
  daily   — 每日进度汇报（默认每天 18:00 执行）
  weekly  — 每周技术雷达扫描（默认周一 09:00 执行）
  check   — 文档一致性检查（随时可执行）

定时方式：
  AI 定时任务：通过 create_scheduled_task 触发，AI 解读结果后更新 PROGRESS.md
  Windows 计划任务：纯脚本任务（如文件备份）
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(r"D:\projects\sci-agent")
SCRIPTS_DIR = PROJECT_ROOT / "scripts"
MANIFEST_PATH = PROJECT_ROOT / "docs" / "MANIFEST.yaml"


def run_daily():
    """每日进度汇报"""
    print("=" * 60)
    print("📋 每日项目状态快照")
    print("=" * 60)

    # 1. Git 当日提交统计
    print("\n--- Git 提交统计 ---")
    result = subprocess.run(
        ["git", "log", "--since=midnight", "--oneline", "--all"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT)
    )
    if result.stdout.strip():
        print(result.stdout.strip())
    else:
        print("今日无提交。")

    # 2. 文件变更统计
    print("\n--- 今日文件变更 ---")
    result = subprocess.run(
        ["git", "diff", "--stat", "HEAD@{yesterday}", "HEAD"],
        capture_output=True, text=True, cwd=str(PROJECT_ROOT), shell=True
    )
    if result.stdout.strip():
        print(result.stdout.strip())
    else:
        print("今日无文件变更。")

    # 3. 文档清单状态
    print("\n--- 文档清单 ---")
    subprocess.run(
        ["python", str(SCRIPTS_DIR / "update_manifest.py"), "--check"],
        cwd=str(PROJECT_ROOT)
    )

    print("\n以上为项目每日快照。请 AI Agent 据此更新 PROGRESS.md 第4节。")


def run_weekly():
    """每周技术雷达扫描 — 检查依赖更新和竞品动态"""
    print("=" * 60)
    print("🔭 每周技术雷达扫描")
    print("=" * 60)

    # 1. Python 依赖过期检查
    print("\n--- Python 依赖状态 ---")
    requirements = PROJECT_ROOT / "requirements.txt"
    if requirements.exists():
        subprocess.run(["pip", "list", "--outdated"], shell=True)
    else:
        print("requirements.txt 不存在，跳过。")

    # 2. Node 依赖过期检查
    package_json = PROJECT_ROOT / "package.json"
    if package_json.exists():
        print("\n--- Node 依赖状态 ---")
        subprocess.run(["npm", "outdated"], cwd=str(PROJECT_ROOT), shell=True)

    print("\n以上为技术雷达扫描结果。")
    print("请 AI Agent 联网搜索以下关键项目的最新动态并生成简报：")
    print("  1. FastAPI 最新版本和新特性")
    print("  2. Next.js 最新版本和新特性")
    print("  3. pgvector 最新进展")
    print("  4. 竞品（ChatGPT/Claude/Perplexity）新发布的科研相关功能")
    print("  5. 科研 AI 工具领域新出现的产品和融资事件")


def run_check():
    """文档一致性检查"""
    print("=" * 60)
    print("🔍 文档一致性检查")
    print("=" * 60)

    # 1. 运行 MANIFEST 更新检查
    subprocess.run(
        ["python", str(SCRIPTS_DIR / "update_manifest.py"), "--check"],
        cwd=str(PROJECT_ROOT)
    )

    # 2. 检查文档内链接有效性
    print("\n--- 文档间引用检查 ---")
    import yaml
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        manifest = yaml.safe_load(f)

    docs = manifest.get("documents", {})
    chains = manifest.get("dependency_chains", [])

    for chain in chains:
        missing = [d for d in chain["chain"] if d not in docs]
        if missing:
            print(f"⚠️ 依赖链断裂: {chain['chain']} 中缺少 {missing}")

    print("\n检查完成。")


if __name__ == "__main__":
    mode = sys.argv[1] if len(sys.argv) > 1 else "daily"

    if mode == "daily":
        run_daily()
    elif mode == "weekly":
        run_weekly()
    elif mode == "check":
        run_check()
    else:
        print(f"未知模式: {mode}。可选: daily / weekly / check")
