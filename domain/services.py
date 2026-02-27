from .entities import (
    Balance,
    Client,
    ContainerTransaction,
    Transaction,
    TransactionLineItem,
)
from .exceptions import InsufficientBalanceError, UnknownContainerTypeError
from .ports import (
    BalanceQueryPort,
    ClientRepositoryPort,
    ContainerTypeRepositoryPort,
    GenericTransactionRepositoryPort,  # new
    TrackingCategoryRepositoryPort,
    TrackingItemRepositoryPort,
    TransactionRepositoryPort,  # still used by old functions
)


async def issue_containers(
    name: str,
    container_type_id: str,
    quantity: int,
    client_repo: ClientRepositoryPort,
    container_type_repo: ContainerTypeRepositoryPort,
    tx_repo: TransactionRepositoryPort,
) -> ContainerTransaction:
    """
    Use case: issue containers to a client (OUT).
    - Validates container type exists.
    - Normalizes client name and auto-assigns client_id.
    - Appends an OUT transaction to the ledger.
    """
    # 1. validate container type exists
    container_type = await container_type_repo.get_by_id(container_type_id)
    if container_type is None:
        raise UnknownContainerTypeError(
            f"Unknown container type '{container_type_id}'."
        )

    # 2. get or create client
    client: Client = await client_repo.get_or_create_by_name(name)

    # 3. create and persist transaction
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
    """
    Use case: record containers returned by a client (IN).
    - Validates container type exists.
    - Enforces OUT - IN >= 0 (cannot return more than owed).
    - Normalizes client name and reuses existing client_id.
    - Appends an IN transaction to the ledger.
    """
    # 1. validate container type exists
    container_type = await container_type_repo.get_by_id(container_type_id)
    if container_type is None:
        raise UnknownContainerTypeError(
            f"Unknown container type '{container_type_id}'."
        )

    # 2. get or create client
    client: Client = await client_repo.get_or_create_by_name(name)

    # 3. check current balance for this client + container type
    current_balance = await balance_query.get_balance_for(client.id, container_type_id)
    if quantity > current_balance:
        raise InsufficientBalanceError(
            client_name=client.name,
            container_type_id=container_type_id,
            balance=current_balance,
            quantity=quantity,
        )

    # 4. create and persist transaction
    tx = ContainerTransaction.receive(client, container_type_id, quantity)
    await tx_repo.save(tx)
    return tx


async def get_current_balances(balance_query: BalanceQueryPort) -> list[Balance]:
    """
    Use case: list all non-zero balances per client + container type.
    - Each balance is SUM(OUT) - SUM(IN).
    - UI can show 'who owes how many of what'.
    """
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
    """
    Generic use case: issue items (OUT) to a client.

    - Validates primary category is balanced.
    - Validates all primary items belong to that category.
    - Enforces OUT - IN >= 0 per (client, item) implicitly via later returns.
    - Secondary items are informational only, no balance.
    """
    # 1. ensure primary category exists and is balanced
    category = await tracking_category_repo.get_by_id(primary_category_id)
    if category is None or not category.is_balanced:
        # domain-level safety: you should not use a non-balanced category as primary
        raise UnknownContainerTypeError(
            f"Invalid primary category '{primary_category_id}' for issuing items."
        )

    # 2. get or create client
    client: Client = await client_repo.get_or_create_by_name(name)

    # 3. load and validate primary items
    line_items: list[TransactionLineItem] = []
    for item_id, qty in primary_item_quantities.items():
        if qty <= 0:
            continue
        item = await tracking_item_repo.get_by_id(item_id)
        if item is None or item.category_id != primary_category_id:
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

    # 4. construct and persist transaction
    tx = Transaction.create(
        client=client,
        direction="OUT",
        line_items=line_items,
        secondary_items=secondary_item_ids,
        notes=notes,
    )
    await tx_repo.save(tx)  # tx_repo will later handle generic Transaction
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
    """
    Generic use case: return items (IN) from a client.

    - Validates primary category is balanced.
    - Validates all primary items belong to that category.
    - Enforces OUT - IN >= 0 per (client_id, tracking_item_id).
    """
    # 1. ensure primary category exists and is balanced
    category = await tracking_category_repo.get_by_id(primary_category_id)
    if category is None or not category.is_balanced:
        raise UnknownContainerTypeError(
            f"Invalid primary category '{primary_category_id}' for returning items."
        )

    # 2. get or create client
    client: Client = await client_repo.get_or_create_by_name(name)

    # 3. load items and enforce balance per item
    line_items: list[TransactionLineItem] = []
    for item_id, qty in primary_item_quantities.items():
        if qty <= 0:
            continue
        item = await tracking_item_repo.get_by_id(item_id)
        if item is None or item.category_id != primary_category_id:
            raise UnknownContainerTypeError(
                f"Unknown or invalid tracking item '{item_id}' for category '{primary_category_id}'."
            )

        # For now, we reuse BalanceQueryPort, but in infra this will need
        # to become item-based instead of container_type-based.
        current_balance = await balance_query.get_balance_for(
            client.id,
            item_id,  # will be adapted once infra is generic
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

    # 4. construct and persist transaction
    tx = Transaction.create(
        client=client,
        direction="IN",
        line_items=line_items,
        secondary_items=secondary_item_ids,
        notes=notes,
    )
    await tx_repo.save(tx)
    return tx
