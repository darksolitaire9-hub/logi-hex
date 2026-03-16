"""v1_fresh_schema

Revision ID: 1bdd180ab367
Revises:
Create Date: 2026-03-16 15:56:17.802661
"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = "1bdd180ab367"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:

    op.create_table(
        "workspaces",
        sa.Column("id", sa.String, nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("mode", sa.String, nullable=False),
        sa.Column("owner_user_id", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "clients",
        sa.Column("id", sa.String, nullable=False),
        sa.Column("workspace_id", sa.String, nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.UniqueConstraint("workspace_id", "name", name="uq_clients_workspace_name"),
    )

    op.create_table(
        "item_groups",
        sa.Column("id", sa.String, nullable=False),
        sa.Column("workspace_id", sa.String, nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
    )

    op.create_table(
        "items",
        sa.Column("id", sa.String, nullable=False),
        sa.Column("workspace_id", sa.String, nullable=False),
        sa.Column("group_id", sa.String, nullable=False),
        sa.Column("label", sa.String, nullable=False),
        sa.Column("unit", sa.String, nullable=False),
        sa.Column(
            "is_active",
            sa.Boolean,
            nullable=False,
            server_default=sa.true(),
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.ForeignKeyConstraint(["group_id"], ["item_groups.id"]),
    )

    op.create_table(
        "tags",
        sa.Column("id", sa.String, nullable=False),
        sa.Column("workspace_id", sa.String, nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("colour", sa.String, nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.UniqueConstraint("workspace_id", "name", name="uq_tags_workspace_name"),
    )

    op.create_table(
        "item_tags",
        sa.Column("item_id", sa.String, nullable=False),
        sa.Column("tag_id", sa.String, nullable=False),
        sa.PrimaryKeyConstraint("item_id", "tag_id"),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"]),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"]),
    )

    op.create_table(
        "movements",
        sa.Column("id", sa.String, nullable=False),
        sa.Column("workspace_id", sa.String, nullable=False),
        sa.Column("direction", sa.String, nullable=False),
        sa.Column("timestamp", sa.DateTime(timezone=True), nullable=False),
        sa.Column("client_id", sa.String, nullable=True),
        sa.Column("client_name", sa.String, nullable=True),
        sa.Column("correction_reason", sa.String, nullable=True),
        sa.Column("notes", sa.String, nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
    )

    op.create_table(
        "movement_line_items",
        sa.Column(
            "id", sa.Integer, primary_key=True, autoincrement=True, nullable=False
        ),
        sa.Column("movement_id", sa.String, nullable=False),
        sa.Column("item_id", sa.String, nullable=False),
        sa.Column("label", sa.String, nullable=False),
        sa.Column("quantity", sa.Numeric(precision=12, scale=4), nullable=False),
        sa.ForeignKeyConstraint(["movement_id"], ["movements.id"]),
        sa.ForeignKeyConstraint(["item_id"], ["items.id"]),
    )

    op.create_table(
        "movement_tags",
        sa.Column("movement_id", sa.String, nullable=False),
        sa.Column("tag_id", sa.String, nullable=False),
        sa.PrimaryKeyConstraint("movement_id", "tag_id"),
        sa.ForeignKeyConstraint(["movement_id"], ["movements.id"]),
        sa.ForeignKeyConstraint(["tag_id"], ["tags.id"]),
    )


def downgrade() -> None:
    op.drop_table("movement_tags")
    op.drop_table("movement_line_items")
    op.drop_table("movements")
    op.drop_table("item_tags")
    op.drop_table("tags")
    op.drop_table("items")
    op.drop_table("item_groups")
    op.drop_table("clients")
    op.drop_table("workspaces")
