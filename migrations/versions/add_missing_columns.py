"""add missing columns: loan.damageNotes, loan.status, file.conditionNotes,
file.barcode, box.colorStatus, user.userType, and fix user.username length

This migration is safe to run against both:
  - Existing databases created by the original migrations (missing these columns)
  - Fresh databases already created by the updated migrations (columns already present)

Revision ID: add_missing_columns
Revises: 78fa44e34295
Create Date: 2026-04-08

"""

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "add_missing_columns"
down_revision = "78fa44e34295"
branch_labels = None
depends_on = None


def _column_exists(table_name, column_name):
    """Return True if the column already exists in the table."""
    bind = op.get_bind()
    insp = sa.inspect(bind)
    cols = [c["name"] for c in insp.get_columns(table_name)]
    return column_name in cols


def upgrade():
    # ── loan table ──────────────────────────────────────────────────────────
    with op.batch_alter_table("loan") as batch_op:
        if not _column_exists("loan", "damageNotes"):
            batch_op.add_column(
                sa.Column("damageNotes", sa.Text(), nullable=True)
            )
        if not _column_exists("loan", "status"):
            batch_op.add_column(
                sa.Column(
                    "status",
                    sa.String(length=20),
                    nullable=False,
                    server_default="Active",
                )
            )

    # ── file table ──────────────────────────────────────────────────────────
    with op.batch_alter_table("file") as batch_op:
        if not _column_exists("file", "conditionNotes"):
            batch_op.add_column(
                sa.Column("conditionNotes", sa.Text(), nullable=True)
            )
        if not _column_exists("file", "barcode"):
            batch_op.add_column(
                sa.Column("barcode", sa.String(length=100), nullable=True)
            )
            try:
                batch_op.create_unique_constraint("uq_file_barcode", ["barcode"])
            except Exception:
                pass  # Constraint may already exist

    # ── box table ───────────────────────────────────────────────────────────
    with op.batch_alter_table("box") as batch_op:
        if not _column_exists("box", "colorStatus"):
            batch_op.add_column(
                sa.Column("colorStatus", sa.String(length=100), nullable=True)
            )

    # ── user table ──────────────────────────────────────────────────────────
    with op.batch_alter_table("user") as batch_op:
        # Fix username column length from 20 -> 100 if needed.
        # SQLite doesn't enforce VARCHAR lengths so this is a no-op there,
        # but it's important for PostgreSQL production databases.
        batch_op.alter_column(
            "username",
            existing_type=sa.String(length=20),
            type_=sa.String(length=100),
            existing_nullable=False,
        )
        if not _column_exists("user", "userType"):
            batch_op.add_column(
                sa.Column(
                    "userType",
                    sa.Boolean(),
                    nullable=False,
                    server_default=sa.false(),
                )
            )


def downgrade():
    bind = op.get_bind()
    insp = sa.inspect(bind)

    with op.batch_alter_table("user") as batch_op:
        if "userType" in [c["name"] for c in insp.get_columns("user")]:
            batch_op.drop_column("userType")
        batch_op.alter_column(
            "username",
            existing_type=sa.String(length=100),
            type_=sa.String(length=20),
            existing_nullable=False,
        )

    with op.batch_alter_table("box") as batch_op:
        if "colorStatus" in [c["name"] for c in insp.get_columns("box")]:
            batch_op.drop_column("colorStatus")

    with op.batch_alter_table("file") as batch_op:
        if "barcode" in [c["name"] for c in insp.get_columns("file")]:
            batch_op.drop_column("barcode")
        if "conditionNotes" in [c["name"] for c in insp.get_columns("file")]:
            batch_op.drop_column("conditionNotes")

    with op.batch_alter_table("loan") as batch_op:
        if "status" in [c["name"] for c in insp.get_columns("loan")]:
            batch_op.drop_column("status")
        if "damageNotes" in [c["name"] for c in insp.get_columns("loan")]:
            batch_op.drop_column("damageNotes")