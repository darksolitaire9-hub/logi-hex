# domain/entities/workspaces.py

from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import uuid4

from domain.language import WorkspaceMode


@dataclass
class Workspace:
    """
    One isolated notebook of movements.
    Mode is set on creation and cannot be changed.
    """

    id: str
    name: str
    mode: WorkspaceMode
    owner_user_id: str
    created_at: datetime

    @classmethod
    def create(
        cls,
        name: str,
        mode: WorkspaceMode,
        owner_user_id: str,
    ) -> "Workspace":
        return cls(
            id=uuid4().hex,
            name=name.strip(),
            mode=mode,
            owner_user_id=owner_user_id,
            created_at=datetime.now(timezone.utc),
        )
