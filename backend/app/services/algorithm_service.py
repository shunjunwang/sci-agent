"""
# mypy: disable-error-code="no-untyped-def"
M9 - 算法商城 业务服务

交付物来源: task-pc3-m9
核心逻辑: 算法注册 → 搜索/浏览 → 沙箱执行 → 评价管理

Mock 策略：数据库查询优先走真实 DB；当 DB 中 Algorithm 表为空时
自动回退到 mock 种子数据（5 个算法，覆盖文本分析/图像处理/数据挖掘/
统计建模/网络分析五大类别），保证前端开发调试不受空库影响。
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List, Tuple

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.algorithm import Algorithm, AlgorithmReview, AlgorithmExecution
from app.models.user import User


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


# ── Mock 数据工厂 ──────────────────────────────

_MOCK_CATEGORIES = ["文本分析", "图像处理", "数据挖掘", "统计建模", "网络分析"]
_MOCK_STATUSES = ["queued", "running", "completed", "failed", "timeout"]
_MOCK_ALGORITHM_COUNT = 30  # 足够覆盖分页测试


def _make_mock_algorithm(idx: int) -> Algorithm:
    cat = _MOCK_CATEGORIES[idx % len(_MOCK_CATEGORIES)]
    return Algorithm(
        id=f"mock-alg-{idx:04d}",
        name=f"Mock算法模板 #{idx} - {cat}",
        description=f"这是 {cat} 方向的第 {idx} 个演示算法模板，适用于相关科研场景的快速验证。",
        category=cat,
        author_id="mock-user-0001",
        docker_image=f"sciagent/mock-algo-{cat.lower().replace(' ', '-')}:v1.0",
        input_schema={"type": "object", "properties": {"lr": {"type": "number", "default": 0.001}}},
        output_schema={"type": "object", "properties": {"accuracy": {"type": "number"}}},
        default_params={"lr": 0.001, "epochs": 100},
        is_public=True,
        usage_count=idx * 13,
        rating_avg=round(3.0 + (idx % 3) * 0.8, 1),
        rating_count=idx * 5,
        created_at=_now_utc(),
        updated_at=_now_utc(),
    )


def _make_mock_execution(idx: int, algorithm_id: str, user_id: str) -> AlgorithmExecution:
    return AlgorithmExecution(
        id=f"mock-exec-{idx:04d}",
        algorithm_id=algorithm_id,
        user_id=user_id,
        sandbox_job_id=f"mock-sbjob-{idx:04d}",
        params={"lr": 0.001},
        input_data={"dataset": "cifar10"},
        output_data={"accuracy": 0.923, "loss": 0.341},
        status=_MOCK_STATUSES[idx % len(_MOCK_STATUSES)],
        execution_time=round(12.5 + idx * 3.1, 2),
        cost=round(0.05 + idx * 0.02, 4),
        created_at=_now_utc(),
    )


class AlgorithmService:
    """算法商城业务服务"""

    # ── 搜索 / 列表 ──────────────────────────────

    @staticmethod
    async def search_algorithms(
        db: AsyncSession,
        keyword: Optional[str] = None,
        category: Optional[str] = None,
        sort_by: str = "newest",
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[Algorithm], int]:
        """搜索/列表算法模板。

        Args:
            db: 数据库会话。
            keyword: 名称关键词搜索。
            category: 分类筛选。
            sort_by: 排序方式 rating / usage / newest。
            skip: 偏移量。
            limit: 返回上限。

        Returns:
            (算法列表, 总数)。
        """
        # ── 1. 先查真实 DB ────────────────────────
        conditions = [Algorithm.is_public]

        if keyword:
            conditions.append(Algorithm.name.ilike(f"%{keyword}%"))  # type: ignore[arg-type]
        if category:
            conditions.append(Algorithm.category == category)  # type: ignore[arg-type]

        count_stmt = select(func.count()).where(and_(*conditions))
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        if total > 0:
            order_map = {
                "rating": Algorithm.rating_avg.desc(),
                "usage": Algorithm.usage_count.desc(),
                "newest": Algorithm.created_at.desc(),
            }
            order_col = order_map.get(sort_by, Algorithm.created_at.desc())

            stmt = (
                select(Algorithm)
                .where(and_(*conditions))
                .order_by(order_col)  # type: ignore[arg-type]
                .offset(skip)
                .limit(limit)
            )
            result = await db.execute(stmt)
            items = list(result.scalars().all())
            return items, total

        # ── 2. DB 无数据，检查是否完全为空 ──────────
        db_total = await db.execute(
            select(func.count()).select_from(Algorithm)
        )
        if (db_total.scalar() or 0) == 0:
            # 数据库为空，回退 mock 种子数据
            all_mock = [_make_mock_algorithm(i + 1) for i in range(_MOCK_ALGORITHM_COUNT)]
            if keyword:
                all_mock = [a for a in all_mock if keyword.lower() in a.name.lower()]
            if category:
                all_mock = [a for a in all_mock if a.category == category]
            total = len(all_mock)
            if sort_by == "rating":
                all_mock.sort(key=lambda a: a.rating_avg, reverse=True)
            elif sort_by == "usage":
                all_mock.sort(key=lambda a: a.usage_count, reverse=True)
            else:
                all_mock.sort(key=lambda a: a.created_at, reverse=True)
            items = all_mock[skip: skip + limit]
            return items, total

        # 有筛选条件但 DB 有数据只是不匹配筛选条件 → 返回空
        return [], 0

    @staticmethod
    async def get_algorithm(db: AsyncSession, algorithm_id: str) -> Optional[Algorithm]:
        """获取算法详情（含评价）。"""
        # ── 先查真实 DB ────────────────────────
        stmt = (
            select(Algorithm)
            .options(selectinload(Algorithm.reviews))
            .where(Algorithm.id == algorithm_id)
        )
        result = await db.execute(stmt)
        alg = result.scalar_one_or_none()
        if alg is not None:
            return alg

        # ── DB 为空时回退 mock ──────────────────
        db_total = await db.execute(
            select(func.count()).select_from(Algorithm)
        )
        if (db_total.scalar() or 0) == 0:
            for i in range(1, _MOCK_ALGORITHM_COUNT + 1):
                if algorithm_id == f"mock-alg-{i:04d}":
                    return _make_mock_algorithm(i)
        return None

    # ── CRUD ──────────────────────────────────────

    @staticmethod
    async def create_algorithm(
        db: AsyncSession, author: User, data: dict
    ) -> Algorithm:
        """注册算法模板。"""
        algorithm = Algorithm(
            id=str(uuid.uuid4()),
            name=data["name"],
            description=data.get("description"),
            category=data["category"],
            author_id=str(author.id),
            docker_image=data["docker_image"],
            input_schema=data.get("input_schema", {}),
            output_schema=data.get("output_schema", {}),
            default_params=data.get("default_params", {}),
            is_public=data.get("is_public", True),
            usage_count=0,
            rating_avg=0.0,
            rating_count=0,
        )
        db.add(algorithm)
        await db.commit()
        await db.refresh(algorithm)
        return algorithm

    @staticmethod
    async def update_algorithm(
        db: AsyncSession, algorithm_id: str, author_id: str, data: dict
    ) -> Optional[Algorithm]:
        """更新算法信息（仅作者）。"""
        stmt = select(Algorithm).where(
            and_(Algorithm.id == algorithm_id, Algorithm.author_id == author_id)
        )
        result = await db.execute(stmt)
        algorithm = result.scalar_one_or_none()
        if not algorithm:
            return None

        updatable = [
            "name", "description", "category", "docker_image",
            "input_schema", "output_schema", "default_params", "is_public",
        ]
        for field in updatable:
            if field in data and data[field] is not None:
                setattr(algorithm, field, data[field])

        algorithm.updated_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(algorithm)
        return algorithm

    @staticmethod
    async def delete_algorithm(
        db: AsyncSession, algorithm_id: str, author_id: str
    ) -> bool:
        """删除算法（仅作者）。"""
        stmt = select(Algorithm).where(
            and_(Algorithm.id == algorithm_id, Algorithm.author_id == author_id)
        )
        result = await db.execute(stmt)
        algorithm = result.scalar_one_or_none()
        if not algorithm:
            return False
        await db.delete(algorithm)
        await db.commit()
        return True

    # ── 执行 ──────────────────────────────────────

    @staticmethod
    async def create_execution(
        db: AsyncSession,
        algorithm: Algorithm,
        user_id: str,
        params: dict,
        input_data: dict,
        sandbox_job_id: Optional[str] = None,
    ) -> AlgorithmExecution:
        """创建算法执行记录。"""
        # ── Mock 算法：直接返回 mock 执行记录 ─────
        if algorithm.id.startswith("mock-alg-"):
            idx = int(algorithm.id.split("-")[-1])
            exec_obj = _make_mock_execution(idx, algorithm.id, user_id)
            exec_obj.params = params
            exec_obj.input_data = input_data
            return exec_obj

        execution = AlgorithmExecution(
            id=str(uuid.uuid4()),
            algorithm_id=algorithm.id,
            user_id=user_id,
            sandbox_job_id=sandbox_job_id,
            params=params,
            input_data=input_data,
            status="queued",
        )
        db.add(execution)
        algorithm.usage_count = (algorithm.usage_count or 0) + 1
        await db.commit()
        await db.refresh(execution)
        return execution

    @staticmethod
    async def update_execution_status(
        db: AsyncSession,
        execution_id: str,
        status: str,
        **kwargs,
    ) -> Optional[AlgorithmExecution]:
        """更新执行记录状态。"""
        stmt = select(AlgorithmExecution).where(AlgorithmExecution.id == execution_id)
        result = await db.execute(stmt)
        execution = result.scalar_one_or_none()
        if not execution:
            return None

        execution.status = status
        for key, value in kwargs.items():
            if value is not None:
                setattr(execution, key, value)

        await db.commit()
        await db.refresh(execution)
        return execution

    @staticmethod
    async def get_execution(db: AsyncSession, execution_id: str) -> Optional[AlgorithmExecution]:
        """查询算法执行记录。"""
        # ── 先查真实 DB ────────────────────────
        stmt = (
            select(AlgorithmExecution)
            .options(selectinload(AlgorithmExecution.sandbox_job))
            .where(AlgorithmExecution.id == execution_id)
        )
        result = await db.execute(stmt)
        exec_obj = result.scalar_one_or_none()
        if exec_obj is not None:
            return exec_obj

        # ── DB 为空时回退 mock ──────────────────
        db_total = await db.execute(
            select(func.count()).select_from(Algorithm)
        )
        if (db_total.scalar() or 0) == 0:
            for i in range(1, 11):
                if execution_id == f"mock-exec-{i:04d}":
                    return _make_mock_execution(i, f"mock-alg-{i:04d}", "mock-user-0001")
        return None

    @staticmethod
    async def list_executions(
        db: AsyncSession,
        user_id: Optional[str] = None,
        algorithm_id: Optional[str] = None,
        status: Optional[str] = None,
        skip: int = 0,
        limit: int = 20,
    ) -> Tuple[List[AlgorithmExecution], int]:
        """分页查询执行历史。

        Args:
            db: 数据库会话。
            user_id: 按用户筛选（不传则返回所有）。
            algorithm_id: 按算法筛选。
            status: 按状态筛选（queued / running / completed / failed / timeout）。
            skip: 偏移量。
            limit: 返回上限。

        Returns:
            (执行记录列表, 总数)。
        """
        # ── 先查真实 DB ────────────────────────
        conditions = []
        if user_id:
            conditions.append(AlgorithmExecution.user_id == user_id)
        if algorithm_id:
            conditions.append(AlgorithmExecution.algorithm_id == algorithm_id)
        if status:
            conditions.append(AlgorithmExecution.status == status)

        count_stmt = select(func.count()).select_from(AlgorithmExecution)
        if conditions:
            count_stmt = count_stmt.where(and_(*conditions))
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        if total > 0:
            stmt = select(AlgorithmExecution).order_by(AlgorithmExecution.created_at.desc())
            if conditions:
                stmt = stmt.where(and_(*conditions))
            stmt = stmt.offset(skip).limit(limit)
            result = await db.execute(stmt)
            items = list(result.scalars().all())
            return items, total

        # ── DB 为空时回退 mock ──────────────────
        db_total = await db.execute(
            select(func.count()).select_from(Algorithm)
        )
        if (db_total.scalar() or 0) == 0:
            all_mock = [
                _make_mock_execution(
                    i + 1,
                    f"mock-alg-{(i % 5) + 1:04d}",
                    f"mock-user-{(i % 3) + 1:04d}",
                )
                for i in range(20)
            ]
            if user_id:
                all_mock = [e for e in all_mock if e.user_id == user_id]
            if algorithm_id:
                all_mock = [e for e in all_mock if e.algorithm_id == algorithm_id]
            if status:
                all_mock = [e for e in all_mock if e.status == status]
            total = len(all_mock)
            all_mock.sort(key=lambda e: e.created_at, reverse=True)
            items = all_mock[skip: skip + limit]
            return items, total

        return [], 0

    # ── 评价 ──────────────────────────────────────

    @staticmethod
    async def get_existing_review(
        db: AsyncSession, algorithm_id: str, user_id: str
    ) -> Optional[AlgorithmReview]:
        """检查用户是否已评价过某算法。"""
        stmt = select(AlgorithmReview).where(
            and_(AlgorithmReview.algorithm_id == algorithm_id, AlgorithmReview.user_id == user_id)
        )
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def add_review(
        db: AsyncSession,
        algorithm_id: str,
        user_id: str,
        rating: int,
        comment: Optional[str] = None,
    ) -> Optional[AlgorithmReview]:
        """添加评价（每人每个算法仅限一次）。"""
        # 检查是否已评价
        existing = await AlgorithmService.get_existing_review(db, algorithm_id, user_id)
        if existing:
            return None

        # 获取算法
        stmt = select(Algorithm).where(Algorithm.id == algorithm_id)
        result = await db.execute(stmt)
        algorithm = result.scalar_one_or_none()
        if not algorithm:
            return None

        # 创建评价
        review = AlgorithmReview(
            id=str(uuid.uuid4()),
            algorithm_id=algorithm_id,
            user_id=user_id,
            rating=rating,
            comment=comment,
        )
        db.add(review)

        # 更新评分统计
        new_count = (algorithm.rating_count or 0) + 1
        old_avg = algorithm.rating_avg or 0
        new_avg = (old_avg * (algorithm.rating_count or 0) + rating) / new_count
        algorithm.rating_avg = round(new_avg, 2)
        algorithm.rating_count = new_count

        await db.commit()
        await db.refresh(review)
        return review

    @staticmethod
    async def get_reviews(
        db: AsyncSession,
        algorithm_id: str,
        skip: int = 0,
        limit: int = 50,
    ) -> Tuple[List[AlgorithmReview], int]:
        """获取算法的评价列表。"""
        count_stmt = (
            select(func.count())
            .where(AlgorithmReview.algorithm_id == algorithm_id)
        )
        total_result = await db.execute(count_stmt)
        total = total_result.scalar() or 0

        stmt = (
            select(AlgorithmReview)
            .where(AlgorithmReview.algorithm_id == algorithm_id)
            .order_by(AlgorithmReview.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(stmt)
        items = list(result.scalars().all())

        return items, total


algorithm_service = AlgorithmService()
