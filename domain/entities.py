from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import uuid4


@dataclass
class ContainerType:
    id: str  # e.g. "white", "round", "glass"
    label: str  # e.g. "White Box", "Round Box", "Big Glass"


@dataclass
class Client:
    id: str  # auto-generated from name e.g. "cshin"
    name: str  # normalized lowercase e.g. "shivam"

    @classmethod
    def from_name(cls, name: str) -> "Client":
        norm = name.lower().strip().replace(" ", "").replace("-", "")
        client_id = f"c{norm[:4].zfill(3)}"
        return cls(id=client_id, name=name.lower().strip())


@dataclass(frozen=True)
class ContainerTransaction:
    id: str
    timestamp: datetime
    client_id: str
    client_name: str
    container_type_id: str
    direction: Literal["OUT", "IN"]  # OUT = issued, IN = returned
    quantity: int

    @classmethod
    def issue(
        cls, client: Client, container_type_id: str, quantity: int
    ) -> "ContainerTransaction":
        return cls(
            id=uuid4().hex,
            timestamp=datetime.now(),
            client_id=client.id,
            client_name=client.name,
            container_type_id=container_type_id,
            direction="OUT",
            quantity=quantity,
        )

    @classmethod
    def receive(
        cls, client: Client, container_type_id: str, quantity: int
    ) -> "ContainerTransaction":
        return cls(
            id=uuid4().hex,
            timestamp=datetime.now(),
            client_id=client.id,
            client_name=client.name,
            container_type_id=container_type_id,
            direction="IN",
            quantity=quantity,
        )


@dataclass
class Balance:
    client_id: str
    client_name: str
    container_type_id: str
    container_label: str
    balance: int  # SUM(OUT) - SUM(IN) — positive means client owes you
