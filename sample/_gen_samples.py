"""Generate the sample PDF invoices/receipts with reportlab.

Run from anywhere: `python sample/_gen_samples.py`. The generated PDFs are
committed so the tool runs out of the box; this script just lets you regenerate
or tweak them. reportlab is only needed here, not to run doc-extract.
"""
from pathlib import Path

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

HERE = Path(__file__).resolve().parent


def _pdf(name, lines):
    c = canvas.Canvas(str(HERE / name), pagesize=letter)
    width, height = letter
    y = height - 72
    for text, size, bold in lines:
        c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
        c.drawString(72, y, text)
        y -= size + 6
    c.showPage()
    c.save()
    print("wrote", name)


def _row(desc, qty, unit, amount):
    return (f"{desc:<34}{qty:>4}  {unit:>10}  {amount:>12}", 10, False)


# 1) Clean invoice — everything reconciles.
_pdf(
    "acme-cloud-invoice.pdf",
    [
        ("ACME Cloud Services, Inc.", 16, True),
        ("1200 Market Street, San Francisco, CA 94103", 9, False),
        ("", 9, False),
        ("INVOICE", 13, True),
        ("Invoice #: ACM-2024-0417", 10, False),
        ("Date: March 15, 2024", 10, False),
        ("Bill To: Northwind Traders", 10, False),
        ("Currency: USD", 10, False),
        ("", 9, False),
        ("Description                        Qty   Unit Price        Amount", 10, True),
        _row("Compute (vCPU-hours)", 500, "0.04", "20.00"),
        _row("Object storage (TB-month)", 3, "23.00", "69.00"),
        _row("Egress bandwidth (TB)", 2, "90.00", "180.00"),
        _row("Support plan (Business)", 1, "99.00", "99.00"),
        ("", 9, False),
        ("Subtotal:                                             368.00", 10, False),
        ("Tax (8.5%):                                            31.28", 10, False),
        ("Total:                                                399.28", 11, True),
        ("", 9, False),
        ("Payment due within 30 days. Thank you for your business.", 8, False),
    ],
)

# 2) Receipt — small, reconciles.
_pdf(
    "blue-ridge-receipt.pdf",
    [
        ("Blue Ridge Hardware", 15, True),
        ("45 Mountain Rd, Asheville, NC 28801", 9, False),
        ("Receipt #: BRH-88213", 10, False),
        ("Date: 2024/04/02", 10, False),
        ("", 9, False),
        ("Item                               Qty   Unit Price        Amount", 10, True),
        _row("Cordless drill 18V", 1, "89.99", "89.99"),
        _row("Drill bit set (29 pc)", 1, "24.50", "24.50"),
        _row("Wood screws 2in (box)", 3, "6.00", "18.00"),
        ("", 9, False),
        ("Subtotal: $132.49", 10, False),
        ("Tax: $9.27", 10, False),
        ("Total: $141.76", 11, True),
        ("Paid: VISA ****4821", 9, False),
    ],
)

# 3) Invoice with a DELIBERATE total mismatch (tax line is wrong) — so a real
#    run demonstrates the reconciliation warning.
_pdf(
    "northwind-invoice.pdf",
    [
        ("Northwind Traders LLC", 16, True),
        ("88 Harbor Ave, Seattle, WA 98104", 9, False),
        ("INVOICE", 13, True),
        ("Invoice No: NW-5521", 10, False),
        ("Invoice Date: 04/18/2024", 10, False),
        ("Currency: USD", 10, False),
        ("", 9, False),
        ("Description                        Qty   Unit Price        Amount", 10, True),
        _row("Consulting (hours)", 12, "150.00", "1800.00"),
        _row("Travel reimbursement", 1, "340.00", "340.00"),
        ("", 9, False),
        ("Subtotal: 2,140.00", 10, False),
        ("Tax (10%): 214.00", 10, False),
        ("Total: 2,154.00", 11, True),  # wrong on purpose: should be 2,354.00
        ("", 9, False),
        ("Remit to account on file. Net 15.", 8, False),
    ],
)
