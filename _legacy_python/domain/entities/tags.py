# domain/entities/tags.py

from dataclasses import dataclass
from uuid import uuid4


@dataclass
class Tag:
    """
    A filter label for items (and optionally movements).
    e.g. frozen, urgent, drinks, takeaway.
    """

    id: str
    workspace_id: str
    name: str  # normalised lowercase
    colour: str | None = None

    @classmethod
    def create(
        cls,
        workspace_id: str,
        name: str,
        colour: str | None = None,
    ) -> "Tag":
        return cls(
            id=uuid4().hex,
            workspace_id=workspace_id,
            name=name.strip().lower(),
            colour=colour,
        )
