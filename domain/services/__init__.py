"""
domain/services — Domain service layer for logi-hex.

This package is split by responsibility. Import directly from here
so callers never need to know which sub-module a function lives in.

    from domain.services import send_items, receive_stock, create_workspace
"""

from domain.services.accounts import collect_items, send_items
from domain.services.clients import get_or_create_client, list_clients
from domain.services.inventory import correct_stock, receive_stock, use_stock
from domain.services.item_groups import create_item_group, list_item_groups
from domain.services.items import (
    archive_item,
    create_item,
    create_item_with_opening_stock,
    list_items,
    reactivate_item,
)
from domain.services.tags import assign_tag_to_item, create_tag, list_tags
from domain.services.workspaces import create_workspace, list_workspaces

__all__ = [
    # workspaces
    "create_workspace",
    "list_workspaces",
    # clients
    "get_or_create_client",
    "list_clients",
    # item groups
    "create_item_group",
    "list_item_groups",
    # items
    "create_item",
    "create_item_with_opening_stock",
    "archive_item",
    "reactivate_item",
    "list_items",
    # tags
    "create_tag",
    "assign_tag_to_item",
    "list_tags",
    # accounts
    "send_items",
    "collect_items",
    # inventory
    "receive_stock",
    "use_stock",
    "correct_stock",
]
