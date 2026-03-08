from .entities import (
    Balance,
    Client,
    ContainerTransaction,
    TrackingCategory,
    TrackingItem,
    Transaction,
    TransactionLineItem,
)
from .exceptions import InsufficientBalanceError, UnknownContainerTypeError
from .ports import (
    BalanceQueryPort,
    ClientRepositoryPort,
    ContainerTypeRepositoryPort,
    GenericTransactionRepositoryPort,
    TrackingCategoryRepositoryPort,
    TrackingItemRepositoryPort,
    TransactionRepositoryPort,
)


async def _ensure_secondary_items_exist(
    tracking_item_repo: TrackingItemRepositoryPort,
    secondary_item_ids: list[str],
) -> None:
    for secondary_id in secondary_item_ids:
        item = await tracking_item_repo.get_by_id(secondary_id)
        # ensure secondary items are active too
        if item is None or not item.is_active:
            raise UnknownContainerTypeError(f"Unknown secondary item '{secondary_id}'.")


async def issue_containers(
    name: str,
    container_type_id: str,
    quantity: int,
    client_repo: ClientRepositoryPort,
    container_type_repo: ContainerTypeRepositoryPort,
    tx_repo: TransactionRepositoryPort,
) -> ContainerTransaction:
    container_type = await container_type_repo.get_by_id(container_type_id)
    if container_type is None:
        raise UnknownContainerTypeError(
            f"Unknown container type '{container_type_id}'."
        )

    client: Client = await client_repo.get_or_create_by_name(name)
    tx = ContainerTransaction.issue(client, container_type_id, quantity)
    await tx_repo.save(tx)
    return tx


async def return_containers(
    name: str,
    container_type_id: str,
    quantity: int,
    client_repo: ClientRepositoryPort,
    container_type_repo: ContainerTypeRepositoryPort,
    tx_repo: TransactionRepositoryPort,
    balance_query: BalanceQueryPort,
) -> ContainerTransaction:
    container_type = await container_type_repo.get_by_id(container_type_id)
    if container_type is None:
        raise UnknownContainerTypeError(
            f"Unknown container type '{container_type_id}'."
        )

    client: Client = await client_repo.get_or_create_by_name(name)

    current_balance = await balance_query.get_balance_for(client.id, container_type_id)
    if quantity > current_balance:
        raise InsufficientBalanceError(
            client_name=client.name,
            container_type_id=container_type_id,
            balance=current_balance,
            quantity=quantity,
        )

    tx = ContainerTransaction.receive(client, container_type_id, quantity)
    await tx_repo.save(tx)
    return tx


async def get_current_balances(balance_query: BalanceQueryPort) -> list[Balance]:
    return await balance_query.get_balances()


async def issue_items(
    name: str,
    primary_item_quantities: dict[str, int],  # tracking_item_id -> quantity
    secondary_item_ids: list[str],
    notes: str | None,
    client_repo: ClientRepositoryPort,
    tracking_item_repo: TrackingItemRepositoryPort,
    tracking_category_repo: TrackingCategoryRepositoryPort,
    tx_repo: GenericTransactionRepositoryPort,
    balance_query: BalanceQueryPort,
    primary_category_id: str,
) -> Transaction:
    category = await tracking_category_repo.get_by_id(primary_category_id)
    if category is None or not category.enforce_returns:
        raise UnknownContainerTypeError(
            f"Invalid primary category '{primary_category_id}' for issuing items."
        )

    client: Client = await client_repo.get_or_create_by_name(name)

    await _ensure_secondary_items_exist(tracking_item_repo, secondary_item_ids)

    line_items: list[TransactionLineItem] = []
    for item_id, qty in primary_item_quantities.items():
        if qty <= 0:
            continue
        item = await tracking_item_repo.get_by_id(item_id)
        # ensure item exists, belongs to category, and is active
        if (
            item is None
            or item.category_id != primary_category_id
            or not item.is_active
        ):
            raise UnknownContainerTypeError(
                f"Unknown or invalid tracking item '{item_id}' for category '{primary_category_id}'."
            )
        line_items.append(
            TransactionLineItem(
                tracking_item_id=item.id,
                label=item.label,
                quantity=qty,
            )
        )

    if not line_items:
        raise ValueError(
            "At least one primary item with positive quantity is required."
        )

    tx = Transaction.create(
        client=client,
        direction="OUT",
        line_items=line_items,
        secondary_items=secondary_item_ids,
        notes=notes,
    )
    await tx_repo.save(tx)
    return tx


async def return_items(
    name: str,
    primary_item_quantities: dict[str, int],
    secondary_item_ids: list[str],
    notes: str | None,
    client_repo: ClientRepositoryPort,
    tracking_item_repo: TrackingItemRepositoryPort,
    tracking_category_repo: TrackingCategoryRepositoryPort,
    tx_repo: GenericTransactionRepositoryPort,
    balance_query: BalanceQueryPort,
    primary_category_id: str,
) -> Transaction:
    category = await tracking_category_repo.get_by_id(primary_category_id)
    if category is None or not category.enforce_returns:
        raise UnknownContainerTypeError(
            f"Invalid primary category '{primary_category_id}' for returning items."
        )

    client: Client = await client_repo.get_or_create_by_name(name)

    await _ensure_secondary_items_exist(tracking_item_repo, secondary_item_ids)

    line_items: list[TransactionLineItem] = []
    for item_id, qty in primary_item_quantities.items():
        if qty <= 0:
            continue
        item = await tracking_item_repo.get_by_id(item_id)
        # ensure item exists, belongs to category, and is active
        if (
            item is None
            or item.category_id != primary_category_id
            or not item.is_active
        ):
            raise UnknownContainerTypeError(
                f"Unknown or invalid tracking item '{item_id}' for category '{primary_category_id}'."
            )

        current_balance = await balance_query.get_balance_for(
            client.id,
            item_id,
        )
        if qty > current_balance:
            raise InsufficientBalanceError(
                client_name=client.name,
                container_type_id=item_id,
                balance=current_balance,
                quantity=qty,
            )

        line_items.append(
            TransactionLineItem(
                tracking_item_id=item.id,
                label=item.label,
                quantity=qty,
            )
        )

    if not line_items:
        raise ValueError(
            "At least one primary item with positive quantity is required."
        )

    tx = Transaction.create(
        client=client,
        direction="IN",
        line_items=line_items,
        secondary_items=secondary_item_ids,
        notes=notes,
    )
    await tx_repo.save(tx)
    return tx


async def soft_delete_tracking_item(
    item_id: str,
    tracking_item_repo: TrackingItemRepositoryPort,
) -> None:
    item = await tracking_item_repo.get_by_id(item_id)
    if item is None:
        return
    item.is_active = False
    await tracking_item_repo.save(item)


async def list_tracking_categories(
    tracking_category_repo: TrackingCategoryRepositoryPort,
) -> list[TrackingCategory]:
    return await tracking_category_repo.list_all()


async def list_active_tracking_items(
    category_id: str,
    tracking_item_repo: TrackingItemRepositoryPort,
) -> list[TrackingItem]:
    items = await tracking_item_repo.list_all_by_category(category_id)
    return [i for i in items if i.is_active]
