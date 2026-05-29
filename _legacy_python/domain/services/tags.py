from domain.entities import Tag
from domain.exceptions import ItemNotFoundError
from domain.ports import (
    ItemRepositoryPort,
    TagRepositoryPort,
    UnitOfWorkPort,
)


async def create_tag(
    workspace_id: str,
    name: str,
    colour: str | None,
    tag_repo: TagRepositoryPort,
    uow: UnitOfWorkPort,
) -> Tag:
    tag = Tag.create(workspace_id=workspace_id, name=name, colour=colour)
    await tag_repo.save(tag)
    await uow.commit()
    return tag


async def assign_tag_to_item(
    workspace_id: str,
    item_id: str,
    tag_id: str,
    item_repo: ItemRepositoryPort,
    tag_repo: TagRepositoryPort,
    uow: UnitOfWorkPort,
) -> None:
    item = await item_repo.get_by_id(workspace_id, item_id)
    if item is None:
        raise ItemNotFoundError(item_id)
    tag = await tag_repo.get_by_id(workspace_id, tag_id)
    if tag is None:
        raise ItemNotFoundError(tag_id)
    await tag_repo.assign_to_item(item_id, tag_id)
    await uow.commit()


async def list_tags(
    workspace_id: str,
    tag_repo: TagRepositoryPort,
) -> list[Tag]:
    return await tag_repo.list_all(workspace_id)
