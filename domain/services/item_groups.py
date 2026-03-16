from domain.entities import ItemGroup
from domain.ports import ItemGroupRepositoryPort, UnitOfWorkPort


async def create_item_group(
    workspace_id: str,
    name: str,
    group_repo: ItemGroupRepositoryPort,
    uow: UnitOfWorkPort,
) -> ItemGroup:
    group = ItemGroup.create(workspace_id=workspace_id, name=name)
    await group_repo.save(group)
    await uow.commit()
    return group


async def list_item_groups(
    workspace_id: str,
    group_repo: ItemGroupRepositoryPort,
) -> list[ItemGroup]:
    return await group_repo.list_all(workspace_id)
