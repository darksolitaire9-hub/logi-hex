from decimal import Decimal

from domain.exceptions import ClientNotFoundError, InsufficientStillOutError


def test_insufficient_still_out_error_message():
    err = InsufficientStillOutError(
        client_name="Alice",
        item_label="Steel Box",
        unit="pcs",
        still_out=Decimal("3"),
        requested=Decimal("5"),
    )
    assert str(err) == "Alice only has 3 pcs of Steel Box. You cannot collect 5 pcs."
    assert err.client_name == "Alice"
    assert err.item_label == "Steel Box"
    assert err.unit == "pcs"
    assert err.still_out == Decimal("3")
    assert err.requested == Decimal("5")


def test_client_not_found_error_message():
    err = ClientNotFoundError("client-123")
    assert str(err) == "Client 'client-123' does not exist in this workspace."
