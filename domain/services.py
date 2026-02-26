from .entities import Balance, Client, ContainerTransaction
from .exceptions import InsufficientBalanceError, UnknownContainerTypeError
from .ports import (
    BalanceQueryPort,
    ClientRepositoryPort,
    ContainerTypeRepositoryPort,
    TransactionRepositoryPort,
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
    current_balance = await balance_query.get_balance_for(
        client.id, container_type_id
    )
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
