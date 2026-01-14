"""
Alembic migration: Create template_definitions and fillable_fields tables

Revision ID: 001_fcj_templates
Created: 2026-01-12
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers
revision = '001_fcj_templates'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create template_definitions table
    op.create_table(
        'template_definitions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_key', sa.String(length=255), nullable=False),
        sa.Column('cycle', sa.String(length=50), nullable=False),
        sa.Column('file_hash_sha256', sa.String(length=64), nullable=False),
        sa.Column('original_path', sa.String(length=500), nullable=False),
        sa.Column('snapshot_path', sa.String(length=500), nullable=False),
        sa.Column('assets_manifest_path', sa.String(length=500), nullable=True),
        sa.Column('stats_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Indices for template_definitions
    op.create_index('ix_template_key_cycle_hash', 'template_definitions', ['template_key', 'cycle', 'file_hash_sha256'], unique=True)
    op.create_index('ix_template_key', 'template_definitions', ['template_key'])
    op.create_index('ix_template_cycle', 'template_definitions', ['cycle'])
    
    # Create fillable_fields table
    op.create_table(
        'fillable_fields',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('template_id', sa.Integer(), nullable=False),
        sa.Column('field_id', sa.String(length=16), nullable=False),
        sa.Column('sheet_name', sa.String(length=255), nullable=False),
        sa.Column('cell_range', sa.String(length=50), nullable=False),
        sa.Column('label', sa.String(length=255), nullable=True),
        sa.Column('inferred_type', sa.String(length=50), nullable=False),
        sa.Column('required', sa.Boolean(), nullable=False, default=True),
        sa.Column('example_value', sa.Text(), nullable=True),
        sa.Column('phase', sa.String(length=50), nullable=True),
        sa.Column('order_index', sa.Integer(), nullable=False, default=0),
        sa.Column('source_metadata_json', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['template_id'], ['template_definitions.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Indices for fillable_fields
    op.create_index('ix_fillable_template_id', 'fillable_fields', ['template_id'])
    op.create_index('ix_fillable_sheet', 'fillable_fields', ['sheet_name'])
    op.create_index('ix_fillable_phase', 'fillable_fields', ['phase'])
    op.create_index('ix_fillable_order', 'fillable_fields', ['order_index'])
    op.create_index('uq_field_stable', 'fillable_fields', ['template_id', 'field_id'], unique=True)


def downgrade():
    op.drop_index('uq_field_stable', table_name='fillable_fields')
    op.drop_index('ix_fillable_order', table_name='fillable_fields')
    op.drop_index('ix_fillable_phase', table_name='fillable_fields')
    op.drop_index('ix_fillable_sheet', table_name='fillable_fields')
    op.drop_index('ix_fillable_template_id', table_name='fillable_fields')
    op.drop_table('fillable_fields')
    
    op.drop_index('ix_template_cycle', table_name='template_definitions')
    op.drop_index('ix_template_key', table_name='template_definitions')
    op.drop_index('ix_template_key_cycle_hash', table_name='template_definitions')
    op.drop_table('template_definitions')
