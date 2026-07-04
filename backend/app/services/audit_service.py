"""
M8 - 防篡改日志 业务服务

交付物来源: task-pc1-m8
核心逻辑: 哈希链验证 + 只追加写入 + 完整性校验报告 + 行为统计
"""
import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import func, select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLogM8, IntegrityCheckM8


# ── HashChain ──────────────────────────────────

class HashChain:
    """SHA-256 哈希链实现"""

    INITIAL_HASH = "0000000000000000000000000000000000000000000000000000000000000000"
    SALT = ""

    @classmethod
    def compute_hash(
        cls, prev_hash: str, user_id: str, action_type: str,
        action_detail: str, created_at: str,
    ) -> str:
        raw = f"{prev_hash}{user_id}{action_type}{action_detail}{created_at}{cls.SALT}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    @classmethod
    def verify_chain(cls, logs: list[dict]) -> dict:
        broken = 0
        anomalies = []
        for i, log in enumerate(logs):
            if i == 0:
                if log["prev_hash"] != cls.INITIAL_HASH:
                    broken += 1
                    anomalies.append({
                        "index": i, "log_id": log.get("id"),
                        "reason": "prev_hash 与根哈希不匹配",
                    })
            else:
                if log["prev_hash"] != logs[i - 1]["current_hash"]:
                    broken += 1
                    anomalies.append({
                        "index": i, "log_id": log.get("id"),
                        "reason": f"prev_hash 与上一条 current_hash 不匹配",
                    })
        verified = len(logs) - broken
        return {"verified": verified, "broken": broken, "anomalies": anomalies}


# ── AuditService ───────────────────────────────

class AuditService:
    """审计日志服务"""

    ACTION_TYPES = [
        "search", "read", "write", "sandbox", "submit",
        "login", "logout", "register", "share", "invite",
    ]

    @classmethod
    def validate_action_type(cls, action_type: str) -> bool:
        return action_type in cls.ACTION_TYPES

    @staticmethod
    def generate_report_uid() -> str:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        rand = uuid.uuid4().hex[:6]
        return f"verify_{ts}_{rand}"

    @staticmethod
    def determine_chain_status(verified: int, broken: int) -> str:
        if broken == 0:
            return "HEALTHY"
        if broken <= max(1, verified * 0.01):
            return "DEGRADED"
        return "BROKEN"

    @staticmethod
    async def get_latest_log(db: AsyncSession) -> Optional[AuditLogM8]:
        stmt = select(AuditLogM8).order_by(AuditLogM8.created_at.desc()).limit(1)
        result = await db.execute(stmt)
        return result.scalar_one_or_none()

    @staticmethod
    async def create_log(
        db: AsyncSession, user_id: str, action_type: str, action_detail: dict,
        ip_address: Optional[str] = None, device_fingerprint: Optional[str] = None,
    ) -> AuditLogM8:
        latest = await AuditService.get_latest_log(db)
        prev_hash = latest.current_hash if latest else HashChain.INITIAL_HASH
        created_at = datetime.now(timezone.utc)
        created_at_iso = created_at.isoformat()

        detail_json = json.dumps(action_detail, sort_keys=True, ensure_ascii=False)
        current_hash = HashChain.compute_hash(
            prev_hash, user_id, action_type, detail_json, created_at_iso
        )

        log = AuditLogM8(
            user_id=user_id, action_type=action_type,
            action_detail=action_detail, prev_hash=prev_hash,
            current_hash=current_hash, ip_address=ip_address,
            device_fingerprint=device_fingerprint, created_at=created_at,
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return log

    @staticmethod
    async def query_logs(
        db: AsyncSession, user_id: Optional[str] = None,
        action_type: Optional[str] = None, date_from: Optional[str] = None,
        date_to: Optional[str] = None, page: int = 1, page_size: int = 20,
    ) -> Tuple[List[AuditLogM8], int]:
        conditions = []
        if user_id:
            conditions.append(AuditLogM8.user_id == user_id)
        if action_type:
            conditions.append(AuditLogM8.action_type == action_type)
        if date_from:
            conditions.append(AuditLogM8.created_at >= date_from)
        if date_to:
            conditions.append(AuditLogM8.created_at <= date_to)

        where_clause = and_(*conditions) if conditions else True

        count_stmt = select(func.count()).where(where_clause)
        total = (await db.execute(count_stmt)).scalar() or 0

        stmt = (
            select(AuditLogM8)
            .where(where_clause)
            .order_by(AuditLogM8.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        result = await db.execute(stmt)
        items = list(result.scalars().all())
        return items, total

    @staticmethod
    async def verify_logs(
        db: AsyncSession, user_id: Optional[str] = None,
        date_from: Optional[str] = None, date_to: Optional[str] = None,
    ) -> dict:
        conditions = []
        if user_id:
            conditions.append(AuditLogM8.user_id == user_id)
        if date_from:
            conditions.append(AuditLogM8.created_at >= date_from)
        if date_to:
            conditions.append(AuditLogM8.created_at <= date_to)

        where_clause = and_(*conditions) if conditions else True
        stmt = select(AuditLogM8).where(where_clause).order_by(AuditLogM8.created_at.asc())
        result = await db.execute(stmt)
        logs = result.scalars().all()

        log_dicts = [
            {"id": l.id, "prev_hash": l.prev_hash, "current_hash": l.current_hash}
            for l in logs
        ]

        verify_result = HashChain.verify_chain(log_dicts)
        status = AuditService.determine_chain_status(
            verify_result["verified"], verify_result["broken"]
        )

        report = IntegrityCheckM8(
            report_uid=AuditService.generate_report_uid(),
            scope_user_id=user_id,
            scope_date_from=date_from,
            scope_date_to=date_to,
            total_logs=len(log_dicts),
            verified_logs=verify_result["verified"],
            broken_chains=verify_result["broken"],
            anomalies=len(verify_result["anomalies"]),
            hash_chain_status=status,
            details=verify_result["anomalies"],
            verified_at=datetime.now(timezone.utc),
        )
        db.add(report)
        await db.commit()

        return {
            "report_id": report.report_uid,
            "scope": {"user_id": user_id, "date_from": date_from, "date_to": date_to},
            "summary": {
                "total_logs": report.total_logs,
                "verified_logs": report.verified_logs,
                "broken_chains": report.broken_chains,
                "anomalies": report.anomalies,
            },
            "hash_chain_status": status,
            "verified_at": report.verified_at.isoformat(),
        }

    @staticmethod
    async def get_statistics(
        db: AsyncSession, date_from: Optional[str] = None,
        date_to: Optional[str] = None, group_by: str = "date",
    ) -> dict:
        conditions = []
        if date_from:
            conditions.append(AuditLogM8.created_at >= date_from)
        if date_to:
            conditions.append(AuditLogM8.created_at <= date_to)
        where_clause = and_(*conditions) if conditions else True

        totals = {}
        for atype in AuditService.ACTION_TYPES:
            count_stmt = select(func.count()).where(
                where_clause, AuditLogM8.action_type == atype,
            )
            totals[f"{atype}_count"] = (await db.execute(count_stmt)).scalar() or 0

        stats = []
        if group_by == "date":
            stmt = (
                select(
                    func.date(AuditLogM8.created_at).label("key"),
                    AuditLogM8.action_type,
                    func.count().label("cnt"),
                )
                .where(where_clause)
                .group_by(func.date(AuditLogM8.created_at), AuditLogM8.action_type)
                .order_by(func.date(AuditLogM8.created_at))
            )
        elif group_by == "user":
            stmt = (
                select(
                    AuditLogM8.user_id.label("key"),
                    AuditLogM8.action_type,
                    func.count().label("cnt"),
                )
                .where(where_clause)
                .group_by(AuditLogM8.user_id, AuditLogM8.action_type)
                .order_by(AuditLogM8.user_id)
            )
        elif group_by == "action_type":
            stmt = (
                select(
                    AuditLogM8.action_type.label("key"),
                    func.count().label("cnt"),
                )
                .where(where_clause)
                .group_by(AuditLogM8.action_type)
                .order_by(AuditLogM8.action_type)
            )
        else:
            stmt = None

        if stmt is not None:
            result = await db.execute(stmt)
            rows = result.all()
            grouped = {}
            for row in rows:
                key = str(row.key)
                if key not in grouped:
                    grouped[key] = {"key": key}
                if group_by == "action_type":
                    grouped[key]["count"] = row.cnt
                else:
                    grouped[key][f"{row.action_type}_count"] = row.cnt
            stats = list(grouped.values())

        return {
            "period": {"from": date_from, "to": date_to},
            "statistics": stats,
            "totals": totals,
        }


audit_service = AuditService()
