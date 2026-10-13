import pytest
from pydantic import ValidationError

from doc_extract import postprocess as pp
from doc_extract.schema import Invoice, LineItem


def test_validates_cleaned_fixture(clean_data):
    inv = Invoice(**pp.clean(clean_data))
    assert inv.vendor == "ACME Cloud Services, Inc."
    assert len(inv.line_items) == 4
    assert isinstance(inv.line_items[0], LineItem)
    assert inv.total == 399.28


def test_empty_invoice_uses_defaults():
    inv = Invoice()
    assert inv.vendor == ""
    assert inv.line_items == []
    assert inv.total is None


def test_coerces_numeric_strings():
    inv = Invoice(subtotal="100", total="110")
    assert inv.subtotal == 100.0 and inv.total == 110.0


def test_rejects_non_numeric_money():
    with pytest.raises(ValidationError):
        Invoice(line_items=[{"description": "x", "qty": "abc"}])
