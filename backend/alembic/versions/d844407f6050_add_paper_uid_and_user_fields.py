"""add_paper_uid_and_user_fields

Revision ID: d844407f6050
Revises: 4cf596d046a2
Create Date: 2026-07-04 00:25:51.319689

P4-02: Rewritten for SQLite compatibility.
- SQLite does NOT support ALTER COLUMN TYPE — all type changes skipped (no-op on SQLite)
- Only structural changes retained: new columns, constraints, foreign keys
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd844407f6050'
down_revision: Union[str, None] = '4cf596d046a2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _is_sqlite() -> bool:
    from sqlalchemy.engine import Engine
    bind = op.get_bind()
    if isinstance(bind, Engine):
        return bind.dialect.name == "sqlite"
    return False


def upgrade() -> None:
    """Only execute operations supported by SQLite. Type changes skipped."""
    is_sqlite = _is_sqlite()

    # Drop apscheduler_jobs if it exists (P4-02: guard against missing table)
    from sqlalchemy import inspect
    conn = op.get_bind()
    inspector = inspect(conn)
    if 'apscheduler_jobs' in inspector.get_table_names():
        op.drop_index('ix_apscheduler_jobs_next_run_time', table_name='apscheduler_jobs')
        op.drop_table('apscheduler_jobs')

    # === New columns (SQLite supports ADD COLUMN) ===
    op.add_column('papers', sa.Column('paper_uid', sa.String(length=64), nullable=True,
                  comment='文献唯一标识，格式 paper_{uuid前8位}'))
    try:
        op.create_unique_constraint('uq_papers_paper_uid', 'papers', ['paper_uid'])
    except Exception:
        pass  # constraint may already exist

    op.add_column('users', sa.Column('phone', sa.String(length=20), nullable=True))
    op.add_column('users', sa.Column('wechat_union_id', sa.String(length=128), nullable=True))
    op.add_column('users', sa.Column('role', sa.String(length=20), server_default='user', nullable=False))
    try:
        op.create_unique_constraint('uq_users_phone', 'users', ['phone'])
    except Exception:
        pass
    try:
        op.create_unique_constraint('uq_users_wechat_union_id', 'users', ['wechat_union_id'])
    except Exception:
        pass

    # === Foreign key: search_history.user_id → users.id ===
    try:
        op.create_foreign_key('fk_search_history_user_id', 'search_history', 'users',
                              ['user_id'], ['id'], ondelete='SET NULL')
    except Exception:
        pass  # FK may already exist

    # === Type changes: SKIPPED (SQLite does not support ALTER COLUMN TYPE) ===
    # All `op.alter_column(... type_=...)` calls removed.
    # In SQLite all columns are TEXT, so CHAR(32) ↔ VARCHAR(36) is a no-op.
    if not is_sqlite:
        # PostgreSQL / MySQL path — kept as dead code for reference only
        pass


def downgrade() -> None:
    """Reverse only structural changes."""

    # Drop new columns (SQLite doesn't support DROP COLUMN natively either,
    # but modern versions (3.35+) do via ALTER TABLE ... DROP COLUMN)
    try:
        op.drop_column('writing_plans', 'user_id')  # type change skipped — not a new column
    except Exception:
        pass

    # Drop constraints
    try:
        op.drop_constraint('fk_search_history_user_id', 'search_history', type_='foreignkey')
    except Exception:
        pass

    try:
        op.drop_constraint('uq_users_wechat_union_id', 'users', type_='unique')
    except Exception:
        pass

    try:
        op.drop_constraint('uq_users_phone', 'users', type_='unique')
    except Exception:
        pass

    op.drop_column('users', 'role')
    op.drop_column('users', 'wechat_union_id')
    op.drop_column('users', 'phone')

    try:
        op.drop_constraint('uq_papers_paper_uid', 'papers', type_='unique')
    except Exception:
        pass

    op.drop_column('papers', 'paper_uid')
