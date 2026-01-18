"""Create onboarding tables: Organization, Cycle, Membership, Invitation

Revision ID: 005
Revises: 004
Create Date: 2026-01-18

This migration creates the foundational tables for FCJ user onboarding system:
- Organization: Multi-tenant support (FCJ, VentureBuilder, Startups)
- Cycle: Execution cycles (Q1, Q2, etc.) within organizations
- Membership: Association of users to org/cycle/role (authorization layer)
- Invitation: Invite flow with expiring tokens and hash-based security
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timedelta

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    """Create onboarding tables"""
    
    # 1. Create organizations table
    op.create_table(
        'organizations',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('type', sa.String(50), nullable=False, server_default='fcj'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='1'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Índices para organizations
    op.create_index('ix_organizations_name', 'organizations', ['name'])
    op.create_index('ix_organizations_is_active', 'organizations', ['is_active'])
    op.create_index('ix_organizations_created_at', 'organizations', ['created_at'])
    
    # 2. Create cycles table
    op.create_table(
        'cycles',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, server_default='active'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('start_date', sa.DateTime(), nullable=True),
        sa.Column('end_date', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Índices para cycles
    op.create_index('ix_cycles_organization_id', 'cycles', ['organization_id'])
    op.create_index('ix_cycles_status', 'cycles', ['status'])
    
    # 3. Create memberships table (CHAVE - user ↔ org ↔ cycle ↔ role)
    op.create_table(
        'memberships',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('user_id', sa.String(100), nullable=False),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('cycle_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='founder'),
        sa.Column('status', sa.String(50), nullable=False, server_default='active', index=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('revoked_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['cycle_id'], ['cycles.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        # Constraint: não permitir duplicação de mesmo user/org/cycle
        sa.UniqueConstraint('user_id', 'organization_id', 'cycle_id', name='uq_user_org_cycle'),
    )
    
    # Índices para memberships
    op.create_index('ix_memberships_user_id', 'memberships', ['user_id'])
    op.create_index('ix_memberships_organization_id', 'memberships', ['organization_id'])
    op.create_index('ix_memberships_cycle_id', 'memberships', ['cycle_id'])
    op.create_index('ix_memberships_status', 'memberships', ['status'])
    
    # 4. Create invitations table (convites com tokens expirando)
    op.create_table(
        'invitations',
        sa.Column('id', sa.Integer(), nullable=False, autoincrement=True),
        sa.Column('email', sa.String(255), nullable=False, index=True),
        sa.Column('token_hash', sa.String(64), nullable=False, unique=True, index=True),
        sa.Column('organization_id', sa.Integer(), nullable=False),
        sa.Column('cycle_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, server_default='founder'),
        sa.Column('status', sa.String(50), nullable=False, server_default='pending', index=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now(), index=True),
        sa.Column('expires_at', sa.DateTime(), nullable=False, index=True),
        sa.Column('used_at', sa.DateTime(), nullable=True),
        sa.Column('invited_by_user_id', sa.String(100), nullable=True),
        sa.Column('invitation_message', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['cycle_id'], ['cycles.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invited_by_user_id'], ['users.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
    )
    
    # Índices para invitations
    op.create_index('ix_invitations_organization_id', 'invitations', ['organization_id'])
    op.create_index('ix_invitations_cycle_id', 'invitations', ['cycle_id'])
    op.create_index('ix_invitations_status', 'invitations', ['status'])
    op.create_index('ix_invitations_email_status', 'invitations', ['email', 'status'])


def downgrade():
    """Rollback: drop onboarding tables"""
    
    # Drop em ordem reversa (respeitar foreign keys)
    op.drop_table('invitations')
    op.drop_table('memberships')
    op.drop_table('cycles')
    op.drop_table('organizations')
