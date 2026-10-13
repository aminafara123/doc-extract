from doc_extract import postprocess as pp
from doc_extract.schema import Invoice


def test_parse_money():
    assert pp.parse_money("$1,234.56") == 1234.56
    assert pp.parse_money("368.00") == 368.0
    assert pp.parse_money(42) == 42.0
    assert pp.parse_money("(45.00)") == -45.0  # accounting negative
    assert pp.parse_money("USD 90") == 90.0
    assert pp.parse_money("") is None
    assert pp.parse_money(None) is None
    assert pp.parse_money("n/a") is None
    assert pp.parse_money(True) is None  # bool is not money


def test_normalize_date():
    assert pp.normalize_date("March 15, 2024") == "2024-03-15"
    assert pp.normalize_date("2024/04/02") == "2024-04-02"
    assert pp.normalize_date("04/18/2024") == "2024-04-18"
    assert pp.normalize_date("12 May 2024") == "2024-05-12"
    assert pp.normalize_date("2024-01-09") == "2024-01-09"
    # unparseable stays as-is (reconcile will flag it)
    assert pp.normalize_date("sometime last spring") == "sometime last spring"


def test_clean_normalizes_nested(mismatch_data):
    cleaned = pp.clean(mismatch_data)
    assert cleaned["date"] == "2024-04-18"
    assert cleaned["subtotal"] == 2140.0
    assert cleaned["line_items"][0]["amount"] == 1800.0


def test_reconcile_clean_passes(clean_data):
    inv = Invoice(**pp.clean(clean_data))
    confidence, warnings = pp.reconcile(inv)
    assert confidence == "high"
    assert warnings == []


def test_reconcile_mismatch_flags(mismatch_data):
    inv = Invoice(**pp.clean(mismatch_data))
    confidence, warnings = pp.reconcile(inv)
    assert confidence == "low"
    assert warnings  # at least one
    assert any("total" in w for w in warnings)


def test_reconcile_flags_line_item_math():
    inv = Invoice(
        date="2024-01-01",
        line_items=[{"description": "x", "qty": 2, "unit_price": 10, "amount": 25}],
    )
    _, warnings = pp.reconcile(inv)
    assert any("qty*unit_price" in w for w in warnings)


def test_reconcile_flags_unnormalized_date():
    inv = Invoice(date="last tuesday")
    _, warnings = pp.reconcile(inv)
    assert any("date" in w for w in warnings)


def test_reconcile_sparse_is_high():
    # only a date, nothing to contradict -> no warnings
    conf, warnings = pp.reconcile(Invoice(date="2024-01-01"))
    assert conf == "high" and warnings == []
