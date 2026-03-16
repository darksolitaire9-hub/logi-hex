from application.facades._base import FacadeBase
from domain.entities import Tag
from domain.services import assign_tag_to_item, create_tag, list_tags


class TagsMixin(FacadeBase):
    async def create_tag(
        self, workspace_id: str, name: str, colour: str | None = None
    ) -> Tag:
        return await create_tag(
            workspace_id=workspace_id,
            name=name,
            colour=colour,
            tag_repo=self._tag_repo,
            uow=self._uow,
        )

    async def assign_tag_to_item(
        self, workspace_id: str, item_id: str, tag_id: str
    ) -> None:
        await assign_tag_to_item(
            workspace_id=workspace_id,
            item_id=item_id,
            tag_id=tag_id,
            item_repo=self._item_repo,
            tag_repo=self._tag_repo,
            uow=self._uow,
        )

    async def list_tags(self, workspace_id: str) -> list[Tag]:
        return await list_tags(workspace_id, self._tag_repo)
