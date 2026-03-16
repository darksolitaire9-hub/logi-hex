# infrastructure/db/tables.py
import sqlalchemy as sa

metadata = sa.MetaData()

clients_table = sa.Table(
    "clients",
    metadata,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column("name", sa.String, unique=True, nullable=False),
)

container_types_table = sa.Table(
    "container_types",
    metadata,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column("label", sa.String, nullable=False),
)

transactions_table = sa.Table(
    "transactions",
    metadata,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column("timestamp", sa.DateTime, nullable=False),
    sa.Column("client_id", sa.String, sa.ForeignKey("clients.id"), nullable=False),
    sa.Column("client_name", sa.String, nullable=False),
    sa.Column(
        "container_type_id",
        sa.String,
        sa.ForeignKey("container_types.id"),
        nullable=True,
    ),
    sa.Column("direction", sa.String, nullable=False),
    sa.Column("quantity", sa.Integer, nullable=False),
    sa.Column("notes", sa.String, nullable=True),
)

tracking_categories_table = sa.Table(
    "tracking_categories",
    metadata,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column("name", sa.String, nullable=False),
    sa.Column("enforce_returns", sa.Boolean, nullable=False, default=True),
)

tracking_items_table = sa.Table(
    "tracking_items",
    metadata,
    sa.Column("id", sa.String, primary_key=True),
    sa.Column(
        "category_id",
        sa.String,
        sa.ForeignKey("tracking_categories.id"),
        nullable=False,
    ),
    sa.Column("label", sa.String, nullable=False),
    sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.true()),
)

transaction_line_items_table = sa.Table(
    "transaction_line_items",
    metadata,
    sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
    sa.Column(
        "transaction_id", sa.String, sa.ForeignKey("transactions.id"), nullable=False
    ),
    sa.Column(
        "tracking_item_id",
        sa.String,
        sa.ForeignKey("tracking_items.id"),
        nullable=False,
    ),
    sa.Column("label", sa.String, nullable=False),
    sa.Column("quantity", sa.Integer, nullable=False),
)

transaction_secondary_items_table = sa.Table(
    "transaction_secondary_items",
    metadata,
    sa.Column(
        "transaction_id", sa.String, sa.ForeignKey("transactions.id"), primary_key=True
    ),
    sa.Column(
        "tracking_item_id",
        sa.String,
        sa.ForeignKey("tracking_items.id"),
        primary_key=True,
    ),
)



