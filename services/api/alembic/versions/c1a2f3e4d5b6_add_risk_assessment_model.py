"""add_risk_assessment_model

Revision ID: c1a2f3e4d5b6
Revises: ab78872c6988
Create Date: 2026-10-24 16:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c1a2f3e4d5b6'
down_revision: Union[str, None] = 'ab78872c6988'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'risk_assessments',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('repository_id', sa.String(length=36), nullable=False),
        sa.Column('commit_sha', sa.String(length=64), nullable=False),
        sa.Column('branch', sa.String(length=128), nullable=False),
        sa.Column('model_version', sa.String(length=64), nullable=False),
        sa.Column('model_type', sa.String(length=32), nullable=False),
        sa.Column('overall_score', sa.Integer(), nullable=False),
        sa.Column('risk_tier', sa.String(length=32), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('has_missing_data', sa.Boolean(), nullable=False),
        sa.Column('feature_weights', sa.JSON(), nullable=False),
        sa.Column('file_assessments', sa.JSON(), nullable=False),
        sa.Column('summary_stats', sa.JSON(), nullable=False),
        sa.Column('analysis_run_id', sa.String(length=36), nullable=True),
        sa.Column('evaluated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('organization_id', sa.String(length=36), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['repository_id'], ['repositories.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_risk_assessments_commit_sha'), 'risk_assessments', ['commit_sha'], unique=False)
    op.create_index(op.f('ix_risk_assessments_organization_id'), 'risk_assessments', ['organization_id'], unique=False)
    op.create_index(op.f('ix_risk_assessments_repository_id'), 'risk_assessments', ['repository_id'], unique=False)
    op.create_index(op.f('ix_risk_assessments_analysis_run_id'), 'risk_assessments', ['analysis_run_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_risk_assessments_analysis_run_id'), table_name='risk_assessments')
    op.drop_index(op.f('ix_risk_assessments_repository_id'), table_name='risk_assessments')
    op.drop_index(op.f('ix_risk_assessments_organization_id'), table_name='risk_assessments')
    op.drop_index(op.f('ix_risk_assessments_commit_sha'), table_name='risk_assessments')
    op.drop_table('risk_assessments')
