from domain import services
from domain.entities import Balance
from domain.ports import (
    BalanceQueryPort,
    ClientRepositoryPort,
    ContainerTypeRepositoryPort,
    TransactionRepositoryPort,
)


class LogiFacade:
    """
    Application façade for container tracking.

    This is what FastAPI (or a CLI, or tests) should talk to.
    It hides all the wiring of repositories + domain services.
    """

    def __init__(
        self,
        client_repo: ClientRepositoryPort,
        container_type_repo: ContainerTypeRepositoryPort,
        tx_repo: TransactionRepositoryPort,
        balance_query: BalanceQueryPort,
    ) -> None:
        self.client_repo = client_repo
        self.container_type_repo = container_type_repo
        self.tx_repo = tx_repo
        self.balance_query = balance_query

    async def issue(self, name: str, container_type_id: str, quantity: int):
        """
        Issue containers to a client (OUT).
        - name: any case, will be normalized (\"Shivam\" == \"shivam \").
        - container_type_id: e.g. \"white\", \"round\" (must exist in container_types).
        - quantity: positive integer.
        """
        # (Optionally: ensure container_type exists here with container_type_repo)
        return await services.issue_containers(
            name=name,
            container_type_id=container_type_id,
            quantity=quantity,
            client_repo=self.client_repo,
            tx_repo=self.tx_repo,
        )

    async def receive(self, name: str, container_type_id: str, quantity: int):
        """
        Record containers returned by a client (IN).
        """
        return await services.return_containers(
            name=name,
            container_type_id=container_type_id,
            quantity=quantity,
            client_repo=self.client_repo,
            tx_repo=self.tx_repo,
        )

    async def balances(self) -> list[Balance]:
        """
        Get all non-zero balances per client + container type.
        """
        return await services.get_current_balances(self.balance_query)
