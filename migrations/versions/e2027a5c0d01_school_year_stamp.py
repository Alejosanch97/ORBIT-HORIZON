"""Agrega School_Year (stamp de año escolar) y marca lo existente como 2026

Revision ID: e2027a5c0d01
Revises: 6f8ea32052cc
Create Date: 2026-11-18 09:30:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e2027a5c0d01'
down_revision = '6f8ea32052cc'
branch_labels = None
depends_on = None

# Tablas que ahora llevan año escolar
TABLES = [
    'lesson_planners',
    'activities_calendar',
    'activity_details_form',
    'class_observations',
    'students_alert',
    'parent_meetings',
]

# Todo lo que existe hoy pertenece al año escolar 2026
LEGACY_YEAR = 2026


def _has_column(table, column):
    insp = sa.inspect(op.get_bind())
    return column in [c['name'] for c in insp.get_columns(table)]


def upgrade():
    for table in TABLES:
        if not _has_column(table, 'School_Year'):
            with op.batch_alter_table(table, schema=None) as batch_op:
                batch_op.add_column(sa.Column('School_Year', sa.Integer(), nullable=True))
                batch_op.create_index(
                    batch_op.f(f'ix_{table}_School_Year'), ['School_Year'], unique=False)
        op.execute(
            f'UPDATE {table} SET "School_Year" = {LEGACY_YEAR} WHERE "School_Year" IS NULL'
        )


def downgrade():
    for table in TABLES:
        if _has_column(table, 'School_Year'):
            with op.batch_alter_table(table, schema=None) as batch_op:
                batch_op.drop_index(batch_op.f(f'ix_{table}_School_Year'))
                batch_op.drop_column('School_Year')
