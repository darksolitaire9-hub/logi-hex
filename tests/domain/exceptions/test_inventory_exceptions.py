from decimal import Decimal

from domain.exceptions import CorrectionReasonRequiredError, InsufficientStockError


def test_insufficient_stock_error_message_empty():
    err = InsufficientStockError(
        item_label="Coke",
        unit="pcs",
        in_stock=Decimal("0"),
        requested=Decimal("5"),
    )
    assert str(err) == "Coke is empty. Receive stock before using it."
    assert err.item_label == "Coke"
    assert err.unit == "pcs"
    assert err.in_stock == Decimal("0")
    assert err.requested == Decimal("5")


def test_insufficient_stock_error_message_non_zero():
    err = InsufficientStockError(
        item_label="Coke",
        unit="pcs",
        in_stock=Decimal("2"),
        requested=Decimal("5"),
    )
    assert str(err) == "Coke is at 2 pcs. You cannot use 5 pcs."
    assert err.in_stock == Decimal("2")
    assert err.requested == Decimal("5")


def test_correction_reason_required_message():
    err = CorrectionReasonRequiredError()
    assert str(err) == "Please select a reason for this correction."
