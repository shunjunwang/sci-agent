"""add_missing_models_20260704

Revision ID: cb1956979998
Revises: d844407f6050
Create Date: 2026-07-04 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cb1956979998'
down_revision: Union[str, None] = 'd844407f6050'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── research_preferences ──
    op.create_table('research_preferences',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('default_citation_style', sa.String(20), server_default='gbt7714', nullable=False),
        sa.Column('preferred_journals', sa.JSON(), nullable=True),
        sa.Column('research_keywords', sa.JSON(), nullable=True),
        sa.Column('writing_language', sa.String(10), server_default='zh', nullable=False),
        sa.Column('auto_save_interval', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_research_preferences_user_id', 'research_preferences', ['user_id'], unique=True)

    # ── session_contexts ──
    op.create_table('session_contexts',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('session_date', sa.Date(), nullable=False),
        sa.Column('daily_summary', sa.Text(), nullable=True),
        sa.Column('search_queries', sa.JSON(), server_default='[]', nullable=False),
        sa.Column('papers_read', sa.JSON(), server_default='[]', nullable=False),
        sa.Column('writing_sessions', sa.JSON(), server_default='[]', nullable=False),
        sa.Column('sandbox_runs', sa.JSON(), server_default='[]', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # ── topic_memories ──
    op.create_table('topic_memories',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('workspace_id', sa.Integer(), nullable=True),
        sa.Column('topic_name', sa.String(200), nullable=False),
        sa.Column('conventions', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('key_papers', sa.JSON(), server_default='[]', nullable=False),
        sa.Column('pitfalls', sa.JSON(), server_default='[]', nullable=False),
        sa.Column('experiment_templates', sa.JSON(), server_default='{}', nullable=False),
        sa.Column('status', sa.String(20), server_default='active', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # ── user_profiles ──
    op.create_table('user_profiles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('research_domains', sa.JSON(), server_default='[]', nullable=False),
        sa.Column('preferred_journals', sa.JSON(), server_default='[]', nullable=False),
        sa.Column('writing_style', sa.String(50), nullable=True),
        sa.Column('preferred_language', sa.String(20), server_default='zh', nullable=False),
        sa.Column('citation_format', sa.String(20), server_default='gbt7714', nullable=False),
        sa.Column('institution', sa.String(200), nullable=True),
        sa.Column('role', sa.String(50), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )

    # ── workflow_instances ──
    op.create_table('workflow_instances',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('workflow_type', sa.String(50), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('steps_json', sa.JSON(), nullable=True),
        sa.Column('current_step', sa.String(50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # ── share_links ──
    op.create_table('share_links',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('document_id', sa.String(36), nullable=False),
        sa.Column('token', sa.String(64), nullable=False),
        sa.Column('expires_at', sa.DateTime(), nullable=False),
        sa.Column('max_access_count', sa.Integer(), nullable=False),
        sa.Column('access_count', sa.Integer(), nullable=False),
        sa.Column('allow_download', sa.Boolean(), nullable=False),
        sa.Column('allow_print', sa.Boolean(), nullable=False),
        sa.Column('watermark_text', sa.String(500), nullable=True),
        sa.Column('require_sms', sa.Boolean(), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['writing_documents.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_share_links_token', 'share_links', ['token'], unique=True)
    op.create_index('ix_share_links_user_id', 'share_links', ['user_id'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_share_links_user_id', table_name='share_links')
    op.drop_index('ix_share_links_token', table_name='share_links')
    op.drop_table('share_links')
    op.drop_table('workflow_instances')
    op.drop_table('user_profiles')
    op.drop_table('topic_memories')
    op.drop_table('session_contexts')
    op.drop_index('ix_research_preferences_user_id', table_name='research_preferences')
    op.drop_table('research_preferences')
