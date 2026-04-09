"""add colorStatus to box table

Revision ID: add_color_status_box
Revises: 78fa44e34295
Create Date: 2026-04-07

"""
from alembic import op
import sqlalchemy as sa

revision = 'add_color_status_box'
down_revision = '78fa44e34295'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('box') as batch_op:
        batch_op.add_column(sa.Column('colorStatus', sa.String(length=100), nullable=True))


def downgrade():
    with op.batch_alter_table('box') as batch_op:
        batch_op.drop_column('colorStatus')