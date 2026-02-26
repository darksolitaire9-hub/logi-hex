class InsufficientBalanceError(Exception):
    """Raised when a client tries to return more containers than they have."""

    def __init__(
        self,
        client_name: str,
        container_type_id: str,
        balance: int,
        quantity: int,
    ):
        self.client_name = client_name
        self.container_type_id = container_type_id
        self.balance = balance
        self.quantity = quantity
        super().__init__(
            f"{client_name} only has {balance} '{container_type_id}' "
            f"containers outstanding, cannot return {quantity}."
        )


class UnknownContainerTypeError(Exception):
    """Referenced container type does not exist in the system."""
    pass
