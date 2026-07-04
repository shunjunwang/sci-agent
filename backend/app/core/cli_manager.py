"""
# mypy: disable-error-code="no-untyped-def"
PC2 M2 通用 CLI 服务管理器
不写死任何特定 CLI 工具，支持动态注册和扩展
"""

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class CLISearchAdapter(Protocol):
    """CLI 搜索适配器协议 - 任何 CLI 工具只需实现此协议即可接入"""

    source_name: str  # 数据源标识，如 "keying"

    async def search(
        self,
        query: str,
        page: int = 1,
        page_size: int = 20,
        author: Optional[str] = None,
        year_from: Optional[int] = None,
        year_to: Optional[int] = None,
        **kwargs,
    ) -> tuple[int, List[Dict[str, Any]]]:
        """搜索文献，返回 (total, results_list)"""
        ...

    async def get_detail(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """获取文献详情"""
        ...

    async def get_pdf_url(self, paper_id: str) -> Optional[str]:
        """获取 PDF 下载链接"""
        ...


class CLIServiceRegistry:
    """CLI 服务注册表 - 管理所有外部 CLI 适配器"""

    def __init__(self):
        self._adapters: Dict[str, CLISearchAdapter] = {}

    def register(self, adapter: CLISearchAdapter) -> None:
        """注册一个 CLI 适配器。重复注册同名 source 时抛出 ValueError。"""
        if adapter.source_name in self._adapters:
            raise ValueError(
                f"CLI adapter '{adapter.source_name}' 已注册，不可重复注册"
            )
        self._adapters[adapter.source_name] = adapter

    def get(self, source_name: str) -> Optional[CLISearchAdapter]:
        """获取已注册的适配器"""
        return self._adapters.get(source_name)

    def list_sources(self) -> List[Dict[str, str]]:
        """列出所有已注册的数据源"""
        return [
            {"id": name, "name": name.capitalize()}
            for name in self._adapters.keys()
        ]

    @property
    def sources(self) -> List[str]:
        """已注册的数据源 ID 列表"""
        return list(self._adapters.keys())


# 全局注册表单例
cli_registry = CLIServiceRegistry()
