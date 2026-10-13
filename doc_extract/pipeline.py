"""Orchestration: document text -> LLM -> schema -> validate -> reconcile -> dict.

Output is explicitly labelled AI-generated: the model reads the document, but
a human must confirm the numbers before anyone acts on them.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from . import llm, postprocess
from .extract import read_document
from .schema import SCHEMA_HINT, Invoice

AI_NOTICE = "AI-generated extraction. A human must review before use."

_SYSTEM = (
    "You extract structured data from invoices and receipts. "
    "Return ONLY a JSON object matching the given schema. "
    "Use null for anything the document does not state. Do not invent values."
)

CSV_COLUMNS = [
    "source", "vendor", "invoice_number", "date", "currency",
    "subtotal", "tax", "total", "line_items", "confidence", "warnings",
]


def extract_invoice(text: str):
    """Run one document's text through the model and the deterministic checks.

    Returns (Invoice, confidence, warnings). Raises llm.LLMError if the model
    is unreachable or returns no JSON, and pydantic.ValidationError if the
    cleaned data doesn't fit the schema.
    """
    messages = [
        {"role": "system", "content": _SYSTEM},
        {
            "role": "user",
            "content": (
                f"Schema:\n{SCHEMA_HINT}\n\nDocument:\n{text}\n\n"
                "Return the JSON object only."
            ),
        },
    ]
    raw = llm.chat(messages)
    data = llm.parse_json_block(raw)
    cleaned = postprocess.clean(data)
    invoice = Invoice(**cleaned)
    confidence, warnings = postprocess.reconcile(invoice)
    return invoice, confidence, warnings


def result_dict(source: str, invoice: Invoice, confidence: str, warnings) -> dict:
    return {
        "source": source,
        "ai_generated": True,
        "notice": AI_NOTICE,
        "confidence": confidence,
        "warnings": warnings,
        "invoice": invoice.model_dump(),
    }


def process_file(path, out_dir: Path, ocr: bool = False) -> dict:
    """Extract one file, write out/<name>.json, return the result dict.

    On any failure returns an error record (never raises) so one bad document
    can't sink a batch.
    """
    path = Path(path)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        text = read_document(path, ocr=ocr)
        if not text.strip():
            raise ValueError("no text found (scanned PDF? try --ocr)")
        invoice, confidence, warnings = extract_invoice(text)
        result = result_dict(path.name, invoice, confidence, warnings)
    except Exception as e:  # noqa: BLE001 - batch resilience is the point
        result = {
            "source": path.name,
            "ai_generated": True,
            "notice": AI_NOTICE,
            "error": f"{type(e).__name__}: {e}",
        }
    (out_dir / f"{path.stem}.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8"
    )
    return result


def _csv_row(result: dict) -> dict:
    inv = result.get("invoice", {})
    return {
        "source": result.get("source", ""),
        "vendor": inv.get("vendor", ""),
        "invoice_number": inv.get("invoice_number", ""),
        "date": inv.get("date", ""),
        "currency": inv.get("currency", ""),
        "subtotal": inv.get("subtotal", ""),
        "tax": inv.get("tax", ""),
        "total": inv.get("total", ""),
        "line_items": len(inv.get("line_items", []) or []),
        "confidence": result.get("confidence", "error" if "error" in result else ""),
        "warnings": " | ".join(result.get("warnings", []))
        or result.get("error", ""),
    }


def write_csv(results, out_path) -> Path:
    """Aggregate all results into one invoices.csv (one row per document)."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        writer.writeheader()
        for r in results:
            writer.writerow(_csv_row(r))
    return out_path


def process_path(target, out_dir="out", ocr: bool = False):
    """Process a file or every supported document in a directory.

    Writes per-file JSON and an aggregate out/invoices.csv. Returns the list of
    result dicts.
    """
    from .extract import SUPPORTED

    target = Path(target)
    out_dir = Path(out_dir)
    if target.is_dir():
        files = sorted(
            p for p in target.iterdir() if p.suffix.lower() in SUPPORTED
        )
    else:
        files = [target]
    results = [process_file(p, out_dir, ocr=ocr) for p in files]
    write_csv(results, out_dir / "invoices.csv")
    return results
