"""CLI: python -m doc_extract sample/ [--out out] [--ocr]"""
from __future__ import annotations

import argparse
import sys

from .pipeline import process_path


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(
        prog="doc_extract",
        description="Extract structured data from invoices/receipts (JSON + CSV).",
    )
    ap.add_argument("target", help="a document, or a folder of documents")
    ap.add_argument("--out", default="out", help="output directory (default: out)")
    ap.add_argument(
        "--ocr",
        action="store_true",
        help="OCR scanned images/PDFs (needs the tesseract binary)",
    )
    args = ap.parse_args(argv)

    results = process_path(args.target, out_dir=args.out, ocr=args.ocr)
    if not results:
        print("No supported documents found.", file=sys.stderr)
        return 1

    for r in results:
        if "error" in r:
            print(f"  ! {r['source']}: {r['error']}")
        else:
            flag = r["confidence"].upper()
            n = len(r["warnings"])
            extra = f" ({n} warning{'s' if n != 1 else ''})" if n else ""
            print(f"  - {r['source']}: {flag}{extra}")
    print(f"\nWrote {len(results)} JSON file(s) + {args.out}/invoices.csv")
    print("Output is AI-generated. Review before use.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
