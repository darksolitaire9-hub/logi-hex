"""
domain/exceptions/shared.py — Exceptions shared across both Accounts and Inventory modes.

Covers:
- WorkspaceNotFoundError: workspace missing or not owned by user.
- WorkspaceModeMismatchError: movement direction invalid for workspace mode.
- ArchivedItemError: movement attempted against an archived item.
- EmptyMovementError: movement submitted with zero total quantity.
- ItemNotFoundError: referenced item does not exist in this workspace.
- ItemGroupNotFoundError: referenced item group does not exist.
- TagNotFoundError: referenced tag does not exist.

Message language: docs/LANGUAGE.md — Error messages.
"""

class WorkspaceNotFoundError(Exception):
    """Raised when a workspace does not exist or does not belong to this user."""

    def __init__(self, workspace_id: str):
        super().__init__(f"Workspace '{workspace_id}' not found.")


class WorkspaceModeMismatchError(Exception):
    """
    Raised when a movement direction is invalid for the workspace mode.
    Internal guard — should not reach the user if routes are correct.
    """

    def __init__(self, direction: str, mode: str):
        super().__init__(f"Direction '{direction}' is not valid in {mode} mode.")


class ArchivedItemError(Exception):
    """Raised when a movement is attempted against an archived item."""

    def __init__(self, item_label: str):
        self.item_label = item_label
        super().__init__(f"{item_label} is archived. Reactivate it to log movements.")


class EmptyMovementError(Exception):
    """Raised when a movement is submitted with no valid line items."""

    def __init__(self):
        super().__init__("Please enter a quantity greater than zero.")


class ItemNotFoundError(Exception):
    """Raised when a referenced item does not exist in this workspace."""

    def __init__(self, item_id: str):
        super().__init__(f"Item '{item_id}' does not exist in this workspace.")


class ItemGroupNotFoundError(Exception):
    """Raised when a referenced item group does not exist in this workspace."""

    def __init__(self, group_id: str):
        super().__init__(f"Item group '{group_id}' does not exist in this workspace.")


class TagNotFoundError(Exception):
    """Raised when a referenced tag does not exist in this workspace."""

    def __init__(self, tag_id: str):
        super().__init__(f"Tag '{tag_id}' does not exist in this workspace.")
