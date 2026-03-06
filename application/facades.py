from domain import services
from domain.entities import (
    Balance,
    ContainerType,
    SummaryResult,
    TrackingCategory,
    TrackingItem,
    Transaction,
)
from domain.ports import (
    BalanceQueryPort,
    ClientRepositoryPort,
    ContainerTypeRepositoryPort,
    GenericTransactionRepositoryPort,
    SummaryQueryPort,
    TrackingCategoryRepositoryPort,
    TrackingItemRepositoryPort,
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
        summary_query: SummaryQueryPort,
        uow: UnitOfWorkPort,
        tracking_category_repo: TrackingCategoryRepositoryPort,
        tracking_item_repo: TrackingItemRepositoryPort,
        generic_tx_repo: GenericTransactionRepositoryPort,
    ) -> None:
        self.client_repo = client_repo
        self.container_type_repo = container_type_repo
        self.tx_repo = tx_repo
        self.balance_query = balance_query
        self.summary_query = summary_query
        self.uow = uow
        self.tracking_category_repo = tracking_category_repo
        self.tracking_item_repo = tracking_item_repo
        self.generic_tx_repo = generic_tx_repo

    async def issue(
        self,
        name: str,
        container_type_id: str,
        quantity: int,
    ):
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

    async def issue_items(
        self,
        name: str,
        primary_item_quantities: dict[str, int],
        secondary_item_ids: list[str],
        notes: str | None,
        primary_category_id: str,
    ) -> Transaction:
        try:
            tx = await services.issue_items(
                name=name,
                primary_item_quantities=primary_item_quantities,
                secondary_item_ids=secondary_item_ids,
                notes=notes,
                client_repo=self.client_repo,
                tracking_item_repo=self.tracking_item_repo,
                tracking_category_repo=self.tracking_category_repo,
                tx_repo=self.generic_tx_repo,
                balance_query=self.balance_query,
                primary_category_id=primary_category_id,
            )
            await self.uow.commit()
            return tx
        except Exception:
            await self.uow.rollback()
            raise

    async def return_items(
        self,
        name: str,
        primary_item_quantities: dict[str, int],
        secondary_item_ids: list[str],
        notes: str | None,
        primary_category_id: str,
    ) -> Transaction:
        try:
            tx = await services.return_items(
                name=name,
                primary_item_quantities=primary_item_quantities,
                secondary_item_ids=secondary_item_ids,
                notes=notes,
                client_repo=self.client_repo,
                tracking_item_repo=self.tracking_item_repo,
                tracking_category_repo=self.tracking_category_repo,
                tx_repo=self.generic_tx_repo,
                balance_query=self.balance_query,
                primary_category_id=primary_category_id,
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

    async def summary(self) -> SummaryResult:
        return await self.summary_query.get_summary()

    async def list_container_types(self) -> list[ContainerType]:
        return await self.container_type_repo.list_all()

    async def create_container_type(self, type_id: str, label: str) -> ContainerType:
        try:
            ct = ContainerType(id=type_id, label=label)
            await self.container_type_repo.save(ct)
            await self.uow.commit()
            return ct
        except Exception:
            await self.uow.rollback()
            raise

    async def create_tracking_category(
        self,
        category_id: str,
        name: str,
        enforce_returns: bool,
    ) -> TrackingCategory:
        try:
            category = TrackingCategory(
                id=category_id,
                name=name,
                enforce_returns=enforce_returns,
            )
            await self.tracking_category_repo.save(category)
            await self.uow.commit()
            return category
        except Exception:
            await self.uow.rollback()
            raise

    async def create_tracking_item(
        self,
        item_id: str,
        label: str,
        category_id: str,
    ) -> TrackingItem:
        try:
            item = TrackingItem(
                id=item_id,
                category_id=category_id,
                label=label,
            )
            await self.tracking_item_repo.save(item)
            await self.uow.commit()
            return item
        except Exception:
            await self.uow.rollback()
            raise
