"""Pydantic schema for an extracted invoice/receipt.

This is both the contract we ask the LLM to fill and the gate every
extraction is validated against before it reaches JSON/CSV output.
"""
from __future__ import annotations

from pydantic import BaseModel, Field


class LineItem(BaseModel):
    description: str = ""
    qty: float | None = None
    unit_price: float | None = None
    amount: float | None = None


class Invoice(BaseModel):
    vendor: str = ""
    invoice_number: str = ""
    date: str = ""  # normalized to ISO YYYY-MM-DD by postprocess when possible
    currency: str = ""
    line_items: list[LineItem] = Field(default_factory=list)
    subtotal: float | None = None
    tax: float | None = None
    total: float | None = None


# The JSON shape handed to the model. Kept as a literal string so the prompt
# and the schema can't drift apart in wording, and so it costs nothing to send.
SCHEMA_HINT = """{
  "vendor": "string",
  "invoice_number": "string",
  "date": "string as printed on the document",
  "currency": "ISO code or symbol, e.g. USD or $",
  "line_items": [
    {"description": "string", "qty": number, "unit_price": number, "amount": number}
  ],
  "subtotal": number,
  "tax": number,
  "total": number
}"""
