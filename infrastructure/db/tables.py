"""
infrastructure/db/tables.py — SQLAlchemy Core table definitions.

Rules:
- No SQLite-specific types. All types are SQLAlchemy generic.
- Quantities use Numeric(12, 4) — never Integer.
- All timestamps are DateTime(timezone=True) — stored as UTC.
- Every entity table has workspace_id as a non-nullable FK.
- Unique constraints are workspace-scoped, not global.
- No legacy tables: container_types, transaction_secondary_items.
"""

import sqlalchemy as sa

metadata = sa.MetaData()


# ── Workspaces ───────────────────────────────────────────────────────────────

workspaces_table = sa.Table(
    "workspaces",
    metadata,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column("name", sa.String, nullable=False),
    sa.Column("mode", sa.String, nullable=False),  # WorkspaceMode enum value
    sa.Column("owner_user_id", sa.String, nullable=False),
    sa.Column(
        "created_at",
        sa.DateTime(timezone=True),
        nullable=False,
    ),
)


# ── Clients ──────────────────────────────────────────────────────────────────

clients_table = sa.Table(
    "clients",
    metadata,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column(
        "workspace_id",
        sa.String,
        sa.ForeignKey("workspaces.id"),
        nullable=False,
    ),
    sa.Column("name", sa.String, nullable=False),  # normalised lowercase
    sa.UniqueConstraint("workspace_id", "name", name="uq_clients_workspace_name"),
)


# ── Item Groups ───────────────────────────────────────────────────────────────

item_groups_table = sa.Table(
    "item_groups",
    metadata,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column(
        "workspace_id",
        sa.String,
        sa.ForeignKey("workspaces.id"),
        nullable=False,
    ),
    sa.Column("name", sa.String, nullable=False),
)


# ── Items ────────────────────────────────────────────────────────────────────

items_table = sa.Table(
    "items",
    metadata,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column(
        "workspace_id",
        sa.String,
        sa.ForeignKey("workspaces.id"),
        nullable=False,
    ),
    sa.Column(
        "group_id",
        sa.String,
        sa.ForeignKey("item_groups.id"),
        nullable=False,
    ),
    sa.Column("label", sa.String, nullable=False),
    sa.Column("unit", sa.String, nullable=False),  # free text: pcs, kg, L, etc.
    sa.Column(
        "is_active",
        sa.Boolean,
        nullable=False,
        server_default=sa.true(),
    ),
)


# ── Tags ─────────────────────────────────────────────────────────────────────

tags_table = sa.Table(
    "tags",
    metadata,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column(
        "workspace_id",
        sa.String,
        sa.ForeignKey("workspaces.id"),
        nullable=False,
    ),
    sa.Column("name", sa.String, nullable=False),  # normalised lowercase
    sa.Column("colour", sa.String, nullable=True),
    sa.UniqueConstraint("workspace_id", "name", name="uq_tags_workspace_name"),
)


# ── Item Tags (many-to-many) ──────────────────────────────────────────────────

item_tags_table = sa.Table(
    "item_tags",
    metadata,
    sa.Column(
        "item_id",
        sa.String,
        sa.ForeignKey("items.id"),
        primary_key=True,
    ),
    sa.Column(
        "tag_id",
        sa.String,
        sa.ForeignKey("tags.id"),
        primary_key=True,
    ),
)


# ── Movements ────────────────────────────────────────────────────────────────

movements_table = sa.Table(
    "movements",
    metadata,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column(
        "workspace_id",
        sa.String,
        sa.ForeignKey("workspaces.id"),
        nullable=False,
    ),
    sa.Column("direction", sa.String, nullable=False),  # MovementDirection enum value
    sa.Column(
        "timestamp",
        sa.DateTime(timezone=True),
        nullable=False,
    ),
    sa.Column("client_id", sa.String, nullable=True),  # Accounts mode only
    sa.Column("client_name", sa.String, nullable=True),  # denormalised for history
    sa.Column(
        "correction_reason", sa.String, nullable=True
    ),  # CorrectionReason or None
    sa.Column("notes", sa.String, nullable=True),
)


# ── Movement Line Items ───────────────────────────────────────────────────────

movement_line_items_table = sa.Table(
    "movement_line_items",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column(
        "movement_id",
        sa.String,
        sa.ForeignKey("movements.id"),
        nullable=False,
    ),
    sa.Column(
        "item_id",
        sa.String,
        sa.ForeignKey("items.id"),
        nullable=False,
    ),
    sa.Column("label", sa.String, nullable=False),  # denormalised for history
    sa.Column(
        "quantity",
        sa.Numeric(precision=12, scale=4),
        nullable=False,
    ),
    # quantity semantics per direction:
    # SEND / RECEIVE / USE  → always positive
    # COLLECT               → always positive (direction implies sign)
    # CORRECT               → delta = actual - current (can be negative)
)


# ── Movement Tags (many-to-many) ──────────────────────────────────────────────

movement_tags_table = sa.Table(
    "movement_tags",
    metadata,
    sa.Column(
        "movement_id",
        sa.String,
        sa.ForeignKey("movements.id"),
        primary_key=True,
    ),
    sa.Column(
        "tag_id",
        sa.String,
        sa.ForeignKey("tags.id"),
        primary_key=True,
    ),
)
