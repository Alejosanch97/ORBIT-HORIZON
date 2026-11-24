"""API key personal de Groq por docente (teachers_users.Groq_API_Key)

Revision ID: f3a9c1d2b027
Revises: e2027a5c0d01
Create Date: 2026-11-24 11:05:00

"""
from alembic import op
import sqlalchemy as sa


revision = 'f3a9c1d2b027'
down_revision = 'e2027a5c0d01'
branch_labels = None
depends_on = None


def _has_column(table, column):
    insp = sa.inspect(op.get_bind())
    return column in [c['name'] for c in insp.get_columns(table)]


def upgrade():
    if not _has_column('teachers_users', 'Groq_API_Key'):
        with op.batch_alter_table('teachers_users', schema=None) as batch_op:
            batch_op.add_column(sa.Column('Groq_API_Key', sa.String(length=255), nullable=True))


def downgrade():
    if _has_column('teachers_users', 'Groq_API_Key'):
        with op.batch_alter_table('teachers_users', schema=None) as batch_op:
            batch_op.drop_column('Groq_API_Key')
