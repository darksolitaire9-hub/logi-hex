from domain.entities import Client
from domain.ports import ClientRepositoryPort, UnitOfWorkPort


async def get_or_create_client(
    workspace_id: str,
    name: str,
    client_repo: ClientRepositoryPort,
    uow: UnitOfWorkPort,
) -> Client:
    """
    Return the existing client with this normalised name in this workspace,
    or create and persist a new one.
    """
    normalised = name.lower().strip()
    existing = await client_repo.get_by_name(workspace_id, normalised)
    if existing is not None:
        return existing
    client = Client.create(workspace_id=workspace_id, name=name)
    await client_repo.save(client)
    await uow.commit()
    return client


async def list_clients(
    workspace_id: str,
    client_repo: ClientRepositoryPort,
) -> list[Client]:
    return await client_repo.list_all(workspace_id)
