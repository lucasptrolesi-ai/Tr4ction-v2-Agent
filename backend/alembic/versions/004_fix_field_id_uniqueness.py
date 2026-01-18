"""Fix field_id uniqueness - per template instead of global

Revision ID: 004
Revises: 003
Create Date: 2026-01-18 12:00:00.000000

Objetivo:
- Remover constraint global de unicidade de field_id
- Criar constraint composto (template_id + field_id)
- Permitir field_id duplicado entre templates diferentes

Risco: BAIXO (constraint apenas, sem perda de dados)
Rollback: Simples - dropa e recria constraint
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    """
    Upgrade path: Remove global unique, add composite unique
    """
    # Drop índice único antigo (global)
    try:
        op.drop_index('uq_field_stable', table_name='fillable_fields')
    except Exception:
        # Se não existir, ignorar
        pass
    
    # Criar novo índice único composto (template_id + field_id)
    op.create_index(
        'uq_field_per_template',
        'fillable_fields',
        ['template_id', 'field_id'],
        unique=True
    )


def downgrade():
    """
    Downgrade path: Remove composite unique, add back global unique
    """
    # Drop índice único novo (composto)
    try:
        op.drop_index('uq_field_per_template', table_name='fillable_fields')
    except Exception:
        pass
    
    # Recria índice único antigo (global)
    # NOTA: Isso pode falhar se houver field_ids duplicados entre templates
    # Nesse caso, executar com `--sql` para revisão manual
    try:
        op.create_index(
            'uq_field_stable',
            'fillable_fields',
            ['field_id'],
            unique=True
        )
    except Exception as e:
        # Registrar erro mas não parar migration
        print(f"⚠️ Downgrade: Não foi possível recriar constraint global: {e}")
        print("   (Provavelmente existem field_ids duplicados entre templates)")
