from application.facades._base import FacadeBase
from domain.entities import Client
from domain.services import get_or_create_client, list_clients


class ClientsMixin(FacadeBase):
    async def get_or_create_client(self, workspace_id: str, name: str) -> Client:
        return await get_or_create_client(
            workspace_id=workspace_id,
            name=name,
            client_repo=self._client_repo,
            uow=self._uow,
        )

    async def list_clients(self, workspace_id: str) -> list[Client]:
        return await list_clients(workspace_id, self._client_repo)
