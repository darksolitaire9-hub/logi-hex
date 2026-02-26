from .entities import Balance, Client, ContainerTransaction
from .ports import (
    BalanceQueryPort,
    ClientRepositoryPort,
    TransactionRepositoryPort,
)


async def issue_containers(
    name: str,
    container_type_id: str,
    quantity: int,
    client_repo: ClientRepositoryPort,
    tx_repo: TransactionRepositoryPort,
) -> ContainerTransaction:
    """
    Use case: issue containers to a client (OUT).
    - Normalizes client name and auto-assigns client_id.
    - Appends an OUT transaction to the ledger.
    """
    client: Client = await client_repo.get_or_create_by_name(name)
    tx = ContainerTransaction.issue(client, container_type_id, quantity)
    await tx_repo.save(tx)
    return tx


async def return_containers(
    name: str,
    container_type_id: str,
    quantity: int,
    client_repo: ClientRepositoryPort,
    tx_repo: TransactionRepositoryPort,
) -> ContainerTransaction:
    """
    Use case: record containers returned by a client (IN).
    - Normalizes client name and reuses existing client_id.
    - Appends an IN transaction to the ledger.
    """
    client: Client = await client_repo.get_or_create_by_name(name)
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
