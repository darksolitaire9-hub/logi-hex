from domain import services
from domain.entities import Balance
from domain.ports import (
    BalanceQueryPort,
    ClientRepositoryPort,
    ContainerTypeRepositoryPort,
    TransactionRepositoryPort,
    UnitOfWorkPort,
)


class LogiFacade:
    def __init__(
        self,
        client_repo: ClientRepositoryPort,
        container_type_repo: ContainerTypeRepositoryPort,
        tx_repo: TransactionRepositoryPort,
        balance_query: BalanceQueryPort,
        uow: UnitOfWorkPort,
    ) -> None:
        self.client_repo = client_repo
        self.container_type_repo = container_type_repo
        self.tx_repo = tx_repo
        self.balance_query = balance_query
        self.uow = uow

    async def issue(self, name: str, container_type_id: str, quantity: int):
        try:
            tx = await services.issue_containers(
                name=name,
                container_type_id=container_type_id,
                quantity=quantity,
                client_repo=self.client_repo,
                container_type_repo=self.container_type_repo,
                tx_repo=self.tx_repo,
            )
            await self.uow.commit()
            return tx
        except Exception:
            await self.uow.rollback()
            raise

    async def receive(self, name: str, container_type_id: str, quantity: int):
        try:
            tx = await services.return_containers(
                name=name,
                container_type_id=container_type_id,
                quantity=quantity,
                client_repo=self.client_repo,
                container_type_repo=self.container_type_repo,
                tx_repo=self.tx_repo,
                balance_query=self.balance_query,
            )
            await self.uow.commit()
            return tx
        except Exception:
            await self.uow.rollback()
            raise

    async def balances(self) -> list[Balance]:
        return await services.get_current_balances(self.balance_query)
