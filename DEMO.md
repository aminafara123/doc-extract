# 60-second demo script

Goal: show messy documents going in and clean, checked data coming out, with the bad total caught.

**0:00 - Setup (say, don't type)**
"Invoices and receipts in, structured JSON and CSV out. A local LLM reads them, then plain Python re-checks every total."

**0:05 - Show the inputs**
```bash
ls sample/
```
Three PDFs and a plain-text receipt. Open `sample/northwind-invoice.pdf` for a second: "this one has a wrong total, on purpose."

**0:15 - Run it**
```bash
make run          # or: ./run.sh sample/
```
Point at the per-file lines: three `HIGH`, and `northwind-invoice.pdf: LOW (1 warning)`.

**0:30 - Show a clean result**
```bash
cat out/acme-cloud-invoice.json
```
Line items, ISO date, `"confidence": "high"`, and the AI-generated notice.

**0:40 - Show the catch**
```bash
cat out/northwind-invoice.json
```
Read the warning aloud: `subtotal 2140.0 + tax 214.0 != total 2154.0`. "The extraction matched the page. The maths didn't, so it's flagged, not trusted."

**0:50 - The spreadsheet**
```bash
column -s, -t out/invoices.csv
```
"One row per document, ready for review. The flagged one is the only row a human needs to open."

**0:58 - Close**
"Tests pass offline with no model and no network: `make test`. Everything runs locally, nothing leaves the machine."
