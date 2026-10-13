"""Deterministic clean-up and reconciliation. No LLM, no network.

Two jobs:
  clean()      normalize a raw extraction dict (dates to ISO, money to floats)
  reconcile()  check the maths and return a confidence flag + warnings

Keeping this separate from the model call is the whole point: the numbers are
checked by code, not trusted from the LLM.
"""
from __future__ import annotations

import re
from datetime import datetime

MONEY_KEYS = ("subtotal", "tax", "total")
# Tolerance for money comparisons: a cent covers float/rounding noise.
TOL = 0.01

# Formats tried in order; first that parses wins.
# ponytail: ambiguous DD/MM vs MM/DD (e.g. 05/06/2024) resolves to the first
# format listed (US MM/DD). Add a locale knob if non-US inputs appear.
_DATE_FORMATS = (
    "%Y-%m-%d", "%Y/%m/%d",
    "%m/%d/%Y", "%d/%m/%Y",
    "%m-%d-%Y", "%d-%m-%Y",
    "%B %d, %Y", "%b %d, %Y", "%B %d %Y", "%b %d %Y",
    "%d %B %Y", "%d %b %Y", "%d-%b-%Y", "%d %b, %Y",
    "%m/%d/%y", "%d/%m/%y",
)


def parse_money(v):
    """'$1,234.56' / '(45.00)' / 1234.5 -> float, or None if not a number.

    Negatives may be a leading '-' or accounting parens. Thousands separators
    and currency symbols are stripped.
    ponytail: assumes dot-decimal (US/UK/intl). European '1.234,56' not handled;
    add a decimal_comma flag if such inputs appear.
    """
    if v is None:
        return None
    if isinstance(v, bool):  # bool is an int subclass; never a money value
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    if not s:
        return None
    neg = s.startswith("(") and s.endswith(")")
    s = re.sub(r"[^\d.\-]", "", s)
    if s in ("", "-", ".", "-.", "-"):
        return None
    try:
        val = float(s)
    except ValueError:
        return None
    return -abs(val) if neg else val


def normalize_date(s):
    """Best-effort to ISO YYYY-MM-DD. Returns original string if unparseable."""
    if not s:
        return s
    raw = str(s).strip()
    for fmt in _DATE_FORMATS:
        try:
            return datetime.strptime(raw, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return raw


def _is_iso(s) -> bool:
    return bool(re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(s or "")))


def clean(raw: dict) -> dict:
    """Return a copy of the raw extraction with dates/money normalized.

    Pure transform: shape is left to Pydantic, warnings are left to reconcile.
    """
    data = dict(raw or {})
    data["date"] = normalize_date(data.get("date", ""))
    for k in MONEY_KEYS:
        if k in data:
            data[k] = parse_money(data[k])
    items = []
    for it in data.get("line_items") or []:
        it = dict(it)
        for k in ("qty", "unit_price", "amount"):
            if k in it:
                it[k] = parse_money(it[k])
        items.append(it)
    data["line_items"] = items
    return data


def reconcile(inv, tol: float = TOL):
    """Check line items vs subtotal/tax/total.

    Returns (confidence, warnings): confidence is "high" when nothing is off,
    else "low". Only fields that are present get checked, so a sparse
    extraction isn't penalized for data the document never had.
    """
    warnings: list[str] = []

    if not _is_iso(inv.date):
        warnings.append(f"date not normalized to ISO: {inv.date!r}")

    amounts = [li.amount for li in inv.line_items if li.amount is not None]
    li_sum = round(sum(amounts), 2) if amounts else None

    # each line: qty * unit_price should equal amount
    for i, li in enumerate(inv.line_items, 1):
        if li.qty is not None and li.unit_price is not None and li.amount is not None:
            expected = round(li.qty * li.unit_price, 2)
            if abs(expected - li.amount) > tol:
                warnings.append(
                    f"line {i} ({li.description or '?'}): qty*unit_price="
                    f"{expected} != amount={li.amount}"
                )

    if li_sum is not None and inv.subtotal is not None:
        if abs(li_sum - inv.subtotal) > tol:
            warnings.append(
                f"line items sum {li_sum} != subtotal {inv.subtotal}"
            )

    if inv.subtotal is not None and inv.total is not None:
        tax = inv.tax or 0.0
        if abs(round(inv.subtotal + tax, 2) - inv.total) > tol:
            warnings.append(
                f"subtotal {inv.subtotal} + tax {tax} != total {inv.total}"
            )
    elif li_sum is not None and inv.total is not None and inv.subtotal is None:
        tax = inv.tax or 0.0
        if abs(round(li_sum + tax, 2) - inv.total) > tol:
            warnings.append(
                f"line items sum {li_sum} + tax {tax} != total {inv.total}"
            )

    confidence = "high" if not warnings else "low"
    return confidence, warnings
