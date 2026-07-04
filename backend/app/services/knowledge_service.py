"""
知识库业务逻辑层（已适配主项目 ORM）。

基于 PC2 M3 交付的服务层，适配主项目的 models/library.py、
models/annotation.py、models/paper.py 模型。

注意：主项目 ORM 缺少 M3 原设计的 read_status / notes / last_read_at
字段，对应功能已做降级适配。
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import UUID, uuid5

from sqlalchemy import select, func, or_, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.annotation import Annotation as MainAnnotation
from app.models.library import UserLibrary as MainUserLibrary
from app.models.paper import Paper as MainPaper
from app.models.user import User as MainUser
from app.schemas.knowledge import (
    CitationFormat,
    CitationGraphOut,
    FolderNode,
    GraphEdge,
    GraphNode,
    KnowledgeSearchResult,
    LibraryPaperCreate,
    LibraryPaperUpdate,
    ReadStatus,
    SearchScope,
)
from app.utils.citation_formatter import format_citation


class KnowledgeService:
    """知识库服务 — 所有操作为异步、依赖数据库会话注入。"""

    # P2-07: 知识库容量限制（可配置上限，默认 5000 篇/用户）
    MAX_PAPERS_PER_USER: int = 5000

    # ── 文献 CRUD ──────────────────────────────────

    # 用于将外部字符串 paper_id 映射到确定性 UUID 的命名空间
    _PAPER_NS = UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")  # DNS namespace

    @classmethod
    def _paper_id_to_uuid(cls, paper_id: str) -> UUID:
        """将外部字符串 paper_id（如 arxiv:2401.12345）映射为确定性 UUID。

        同一 paper_id 每次调用产生相同 UUID，确保幂等。
        """
        return uuid5(cls._PAPER_NS, f"sciagent:{paper_id}")

    @classmethod
    def _paper_uuid_to_str(cls, db_paper: MainPaper) -> str:
        """从 DB Paper 对象反推外部 paper_id。"""
        return getattr(db_paper, "openalex_id", None) or str(db_paper.id)

    @classmethod
    async def _get_or_create_paper(
        cls, db: AsyncSession, paper_id: str
    ) -> MainPaper:
        """通过字符串 paper_id 查找或创建 Paper 记录。

        先用确定性 UUID 查找；未命中则创建新记录（将原始字符串存入 openalex_id）。
        """
        paper_uuid = cls._paper_id_to_uuid(paper_id)
        stmt = select(MainPaper).where(MainPaper.id == paper_uuid)
        result = await db.execute(stmt)
        paper = result.scalar_one_or_none()
        if paper:
            return paper

        paper = MainPaper(
            id=paper_uuid,
            title="(待加载)",
            openalex_id=paper_id,
            source_db="openalex",
            search_source=paper_id.split(":")[0] if ":" in paper_id else "unknown",
        )
        db.add(paper)
        await db.flush()
        return paper

    @staticmethod
    async def add_paper(
        db: AsyncSession, user_id: int, data: LibraryPaperCreate
    ) -> MainUserLibrary:
        """添加文献到知识库，重复添加抛出 ValueError。

        paper_id 接受外部字符串标识符（如 arxiv:2401.12345），
        内部通过确定性 UUID 映射到 papers 表。
        超过 MAX_PAPERS_PER_USER 时抛出 ValueError("CAPACITY_EXCEEDED")。
        """
        paper = await KnowledgeService._get_or_create_paper(db, data.paper_id)
        user_uuid = UUID(int=user_id)

        # P2-07: 容量检查
        count_stmt = select(func.count()).where(
            MainUserLibrary.user_id == user_uuid
        )
        current_count = (await db.execute(count_stmt)).scalar() or 0
        if current_count >= cls.MAX_PAPERS_PER_USER:
            raise ValueError("CAPACITY_EXCEEDED")

        existing = await db.execute(
            select(MainUserLibrary).where(
                MainUserLibrary.user_id == user_uuid,
                MainUserLibrary.paper_id == paper.id,
            )
        )
        if existing.scalar_one_or_none():
            raise ValueError("DUPLICATE")

        entry = MainUserLibrary(
            user_id=user_uuid,
            paper_id=paper.id,
            folder_name=data.folder,
            tags=data.tags if data.tags else None,
        )
        db.add(entry)
        await db.commit()

        # 重新查询以 eager-load paper 关系，避免 _build_library_out 等同步调用方
        # 访问 entry.paper 时触发 async lazy load → MissingGreenlet
        stmt = (
            select(MainUserLibrary)
            .where(MainUserLibrary.id == entry.id)
            .options(selectinload(MainUserLibrary.paper))
        )
        result = await db.execute(stmt)
        return result.scalar_one()

    @staticmethod
    async def list_papers(
        db: AsyncSession,
        user_id: int,
        folder: Optional[str] = None,
        tag: Optional[str] = None,
        read_status: Optional[ReadStatus] = None,
        is_favorited: Optional[bool] = None,
        sort_by: str = "added_at",
        order: str = "desc",
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[MainUserLibrary], int]:
        """分页查询知识库文献，支持多维度筛选。"""
        user_uuid = UUID(int=user_id)
        conditions = [MainUserLibrary.user_id == user_uuid]

        if folder:
            conditions.append(MainUserLibrary.folder_name == folder)
        if tag:
            # 主项目 tags 为 Optional[dict]，此处做 JSON 字典模糊匹配
            conditions.append(
                MainUserLibrary.tags.cast(String).like(f"%{tag}%")
            )
        if read_status:
            # 主项目无 read_status，用 is_read 映射
            is_read_val = read_status != ReadStatus.unread
            conditions.append(MainUserLibrary.is_read == is_read_val)
        if is_favorited is not None:
            conditions.append(MainUserLibrary.is_favorite == is_favorited)

        # 总数
        count_stmt = select(func.count()).where(and_(*conditions))
        total = (await db.execute(count_stmt)).scalar() or 0

        # 排序
        sort_col = getattr(MainUserLibrary, sort_by, MainUserLibrary.added_at)
        if order == "asc":
            sort_col = sort_col.asc()
        else:
            sort_col = sort_col.desc()

        stmt = (
            select(MainUserLibrary)
            .where(and_(*conditions))
            .options(selectinload(MainUserLibrary.paper))
            .order_by(sort_col)
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await db.execute(stmt)
        items = list(result.scalars().all())

        return items, total

    @staticmethod
    async def get_paper(
        db: AsyncSession, user_id: int, library_id: int
    ) -> Optional[MainUserLibrary]:
        """获取单条知识库条目。"""
        user_uuid = UUID(int=user_id)
        lib_uuid = UUID(int=library_id)
        stmt = select(MainUserLibrary).where(
            MainUserLibrary.id == lib_uuid,
            MainUserLibrary.user_id == user_uuid,
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def update_paper(
        db: AsyncSession, user_id: int, library_id: int, data: LibraryPaperUpdate
    ) -> Optional[MainUserLibrary]:
        """更新知识库条目。

        主项目 ORM 字段映射：
        - folder → folder_name
        - is_favorited → is_favorite
        - read_status (str) → is_read (bool)
        - notes → 不支持（主项目 ORM 无此字段）
        """
        entry = await KnowledgeService.get_paper(db, user_id, library_id)
        if not entry:
            return None

        update_data = data.model_dump(exclude_unset=True)
        field_map = {
            "folder": "folder_name",
            "is_favorited": "is_favorite",
            "read_status": None,   # 特殊处理
            "notes": None,          # 主项目 ORM 不支持
        }

        for key, value in update_data.items():
            if key in ("notes",):
                continue  # 主项目 ORM 无此字段
            if key == "read_status":
                entry.is_read = (value != "unread")
            elif key in field_map and field_map[key]:
                setattr(entry, field_map[key], value)
            else:
                setattr(entry, key, value)

        await db.commit()
        await db.refresh(entry)
        return entry

    @staticmethod
    async def delete_paper(
        db: AsyncSession, user_id: int, library_id: int
    ) -> bool:
        """删除知识库条目。"""
        entry = await KnowledgeService.get_paper(db, user_id, library_id)
        if not entry:
            return False
        await db.delete(entry)
        await db.commit()
        return True

    @staticmethod
    async def record_read(
        db: AsyncSession, user_id: int, library_id: int
    ) -> None:
        """记录阅读时间（降级：仅标记 is_read）。"""
        entry = await KnowledgeService.get_paper(db, user_id, library_id)
        if entry:
            entry.is_read = True
            await db.commit()

    # ── 全文搜索 ──────────────────────────────────

    @staticmethod
    async def search(
        db: AsyncSession,
        user_id: int,
        q: str,
        search_in: SearchScope = SearchScope.all,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[KnowledgeSearchResult], int]:
        """全文关键词搜索（标题/摘要）。

        注意：主项目 ORM 无 notes 字段，搜索范围不含笔记。
        """
        from sqlalchemy import String

        user_uuid = UUID(int=user_id)
        q_pattern = f"%{q}%"
        conditions = [MainUserLibrary.user_id == user_uuid]

        scope_conditions = []
        if search_in in (SearchScope.all, SearchScope.title):
            scope_conditions.append(MainPaper.title.ilike(q_pattern))
        if search_in in (SearchScope.all, SearchScope.abstract):
            scope_conditions.append(MainPaper.abstract.ilike(q_pattern))

        if scope_conditions:
            conditions.append(or_(*scope_conditions))

        count_stmt = (
            select(func.count(MainUserLibrary.id))
            .join(MainPaper, MainUserLibrary.paper_id == MainPaper.id)
            .where(and_(*conditions))
        )
        total = (await db.execute(count_stmt)).scalar() or 0

        stmt = (
            select(MainUserLibrary)
            .join(MainPaper, MainUserLibrary.paper_id == MainPaper.id)
            .where(and_(*conditions))
            .order_by(MainUserLibrary.added_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await db.execute(stmt)
        entries = list(result.scalars().all())

        items: List[KnowledgeSearchResult] = []
        for entry in entries:
            if not entry.paper:
                continue
            paper_title = entry.paper.title or ""
            paper_abstract = entry.paper.abstract or ""

            match_in = "title"
            snippet = ""
            if paper_title and q.lower() in paper_title.lower():
                match_in = "title"
                snippet = paper_title
            elif paper_abstract and q.lower() in paper_abstract.lower():
                match_in = "abstract"
                idx = paper_abstract.lower().find(q.lower())
                start = max(0, idx - 60)
                end = min(len(paper_abstract), idx + len(q) + 60)
                snippet = paper_abstract[start:end]
            else:
                snippet = paper_title or paper_abstract or ""

            items.append(
                KnowledgeSearchResult(
                    library_id=_uuid_to_int(entry.id),
                    paper_title=paper_title,
                    match_in=match_in,
                    snippet=snippet,
                    relevance_score=1.0,
                )
            )

        return items, total

    # ── 文件夹管理 ─────────────────────────────────

    @staticmethod
    async def get_folders(
        db: AsyncSession, user_id: int
    ) -> List[FolderNode]:
        """获取文件夹树（从 UserLibrary.folder_name 字段聚合）。"""
        user_uuid = UUID(int=user_id)
        stmt = (
            select(
                MainUserLibrary.folder_name,
                func.count(MainUserLibrary.id),
            )
            .where(
                MainUserLibrary.user_id == user_uuid,
                MainUserLibrary.folder_name.isnot(None),
            )
            .group_by(MainUserLibrary.folder_name)
        )
        result = await db.execute(stmt)
        rows = result.all()

        tree: dict[str, FolderNode] = {}
        for folder_path, count in rows:
            parts = folder_path.split("/")
            for i in range(len(parts)):
                partial = "/".join(parts[: i + 1])
                if partial not in tree:
                    tree[partial] = FolderNode(path=partial, count=0, children=[])
            tree[folder_path].count = count

        for full_path, node in tree.items():
            if "/" in full_path:
                parent_path = "/".join(full_path.split("/")[:-1])
                if parent_path in tree and node not in tree[parent_path].children:
                    tree[parent_path].children.append(node)

        roots = [n for p, n in tree.items() if "/" not in p]
        return roots

    @staticmethod
    async def create_folder(
        db: AsyncSession, user_id: int, path: str
    ) -> None:
        """创建文件夹（校验路径合法性，由 folder_name 字段聚合体现）。"""
        if not path or len(path) > 500:
            raise ValueError("INVALID_PATH")

    # ── 批注管理（适配主项目 Annotation 模型）───

    @staticmethod
    async def add_annotation(
        db: AsyncSession,
        user_id: int,
        library_id: int,
        highlighted_text: Optional[str],
        note: str,
        position: Optional[dict],
    ) -> MainAnnotation:
        """添加批注。

        主项目 Annotation 链接到 paper_id（非 library_id），
        因此先从 UserLibrary 查 paper_id。
        """
        entry = await KnowledgeService.get_paper(db, user_id, library_id)
        if not entry:
            raise ValueError("LIBRARY_ENTRY_NOT_FOUND")

        user_uuid = UUID(int=user_id)
        annotation = MainAnnotation(
            user_id=user_uuid,
            paper_id=entry.paper_id,
            content=f"{highlighted_text or ''}\n\n[批注] {note}",
            highlight_range=position,
        )
        db.add(annotation)
        await db.commit()
        await db.refresh(annotation)
        return annotation

    @staticmethod
    async def list_annotations(
        db: AsyncSession, user_id: int, library_id: int
    ) -> List[MainAnnotation]:
        """获取指定知识库条目的所有批注。

        先将 library_id 转换为 paper_id，再查询批注。
        """
        entry = await KnowledgeService.get_paper(db, user_id, library_id)
        if not entry:
            return []
        user_uuid = UUID(int=user_id)
        stmt = select(MainAnnotation).where(
            MainAnnotation.user_id == user_uuid,
            MainAnnotation.paper_id == entry.paper_id,
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())

    @staticmethod
    async def delete_annotation(
        db: AsyncSession, user_id: int, annotation_id: int
    ) -> bool:
        """删除批注。"""
        user_uuid = UUID(int=user_id)
        ann_uuid = UUID(int=annotation_id)
        stmt = select(MainAnnotation).where(
            MainAnnotation.id == ann_uuid,
            MainAnnotation.user_id == user_uuid,
        )
        result = await db.execute(stmt)
        annotation = result.scalar_one_or_none()
        if not annotation:
            return False
        await db.delete(annotation)
        await db.commit()
        return True

    # ── 引用导出 ──────────────────────────────────

    @staticmethod
    async def export_citation(
        db: AsyncSession,
        user_id: int,
        library_ids: List[int],
        fmt: CitationFormat,
    ) -> str:
        """批量导出引用格式字符串。"""
        user_uuid = UUID(int=user_id)
        lib_uuids = [UUID(int=lid) for lid in library_ids]
        stmt = select(MainUserLibrary).where(
            MainUserLibrary.user_id == user_uuid,
            MainUserLibrary.id.in_(lib_uuids),
        )
        result = await db.execute(stmt)
        entries = result.scalars().all()

        citations = []
        for i, entry in enumerate(entries):
            p = entry.paper
            if not p:
                continue
            paper_meta = {
                "title": p.title or "",
                "authors": p.authors if isinstance(p.authors, list) else [],
                "journal": getattr(p, "journal", "") or "",
                "year": getattr(p, "year", None),
                "volume": getattr(p, "volume", "") or "",
                "issue": getattr(p, "issue", "") or "",
                "pages": getattr(p, "pages", "") or "",
                "doi": getattr(p, "doi", "") or "",
            }
            citations.append(format_citation(paper_meta, fmt, index=i + 1))

        return "\n\n".join(citations)

    # ── 引用图谱 ──────────────────────────────────

    @staticmethod
    async def citation_graph(
        db: AsyncSession, user_id: int, library_id: int
    ) -> CitationGraphOut:
        """生成以指定文献为中心的引用关系图谱。"""
        entry = await KnowledgeService.get_paper(db, user_id, library_id)
        if not entry or not entry.paper:
            return CitationGraphOut()

        paper = entry.paper
        center_id = f"paper:{_uuid_to_int(entry.paper_id)}"
        center_label = paper.title or f"Paper {paper.id}"

        nodes = [GraphNode(id=center_id, label=center_label, group="center")]
        edges: list[GraphEdge] = []

        references = getattr(paper, "references", None)
        if references and isinstance(references, list):
            for ref in references:
                ref_id = f"ref:{ref.get('doi', ref.get('id', ''))}"
                if not ref_id.replace("ref:", ""):
                    continue
                ref_label = ref.get("title", "Untitled Reference")
                nodes.append(GraphNode(id=ref_id, label=ref_label, group="reference"))
                edges.append(GraphEdge(source=center_id, target=ref_id, relation="cites"))

        return CitationGraphOut(nodes=nodes, edges=edges)

    # ── 阅读历史 ──────────────────────────────────

    @staticmethod
    async def reading_history(
        db: AsyncSession, user_id: int, days: int = 30, limit: int = 50
    ) -> List[MainUserLibrary]:
        """获取最近的阅读历史。

        主项目 ORM 无 last_read_at，降级为按 added_at 降序返回。
        """
        user_uuid = UUID(int=user_id)
        stmt = (
            select(MainUserLibrary)
            .where(MainUserLibrary.user_id == user_uuid)
            .order_by(MainUserLibrary.added_at.desc())
            .limit(limit)
        )
        result = await db.execute(stmt)
        return list(result.scalars().all())


def _uuid_to_int(uuid_val: UUID) -> int:
    """将 UUID 转换为 int（取 hash 的后 32 位）。

    用于兼容 M3 API 返回的 int 型 ID。
    """
    return abs(hash(uuid_val)) & 0x7FFFFFFF
