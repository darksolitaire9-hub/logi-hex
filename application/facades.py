from domain import services
from domain.entities import (
    Balance,
    Client,
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

    async def create_tracking_item(
        self,
        item_id: str,
        label: str,
        category_id: str,
    ) -> TrackingItem:
        try:
            existing = await self.tracking_item_repo.get_by_category_and_label(
                category_id=category_id,
                label=label,
            )

            if existing is not None:
                existing.is_active = True
                existing.label = label
                await self.tracking_item_repo.save(existing)
                await self.uow.commit()
                return existing

            item = TrackingItem(
                id=item_id,
                category_id=category_id,
                label=label,
                is_active=True,
            )
            await self.tracking_item_repo.save(item)
            await self.uow.commit()
            return item
        except Exception:
            await self.uow.rollback()
            raise

    async def delete_tracking_item(self, item_id: str) -> None:
        try:
            await services.soft_delete_tracking_item(
                item_id=item_id,
                tracking_item_repo=self.tracking_item_repo,
            )
            await self.uow.commit()
        except Exception:
            await self.uow.rollback()
            raise

    async def list_tracking_categories(self) -> list[TrackingCategory]:
        return await services.list_tracking_categories(self.tracking_category_repo)

    async def list_active_tracking_items(self, category_id: str) -> list[TrackingItem]:
        return await services.list_active_tracking_items(
            category_id, self.tracking_item_repo
        )

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

    async def get_client_transactions(self, client_id: str) -> list[Transaction]:
        return await self.generic_tx_repo.get_by_client_id(client_id)

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

    async def list_clients(self) -> list[Client]:
        return await services.list_clients(self.client_repo)
