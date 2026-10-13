"""Get plain text out of a document. PDFs and .txt work out of the box;
scanned images/PDFs need optional OCR (tesseract + pytesseract).

All heavy imports are lazy so the package imports (and tests run) without
pdfplumber, Pillow, or tesseract present.
"""
from __future__ import annotations

from pathlib import Path

PDF_EXTS = {".pdf"}
TEXT_EXTS = {".txt"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".bmp"}
SUPPORTED = PDF_EXTS | TEXT_EXTS | IMAGE_EXTS


class ExtractError(RuntimeError):
    pass


def read_document(path, ocr: bool = False) -> str:
    """Return the text of one document. `ocr=True` enables pytesseract fallback."""
    path = Path(path)
    ext = path.suffix.lower()
    if ext in TEXT_EXTS:
        return path.read_text(encoding="utf-8", errors="replace")
    if ext in PDF_EXTS:
        text = _pdf_text(path)
        if text.strip():
            return text
        if ocr:
            return _ocr_pdf(path)
        return text  # empty: likely a scanned PDF; caller warns, try --ocr
    if ext in IMAGE_EXTS:
        if not ocr:
            raise ExtractError(
                f"{path.name} is an image; rerun with --ocr (needs tesseract)."
            )
        return _ocr_image(path)
    raise ExtractError(f"Unsupported file type: {path.name}")


def _pdf_text(path: Path) -> str:
    try:
        import pdfplumber
    except ImportError as e:  # pragma: no cover - env guard
        raise ExtractError("pdfplumber not installed: pip install pdfplumber") from e
    out = []
    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            out.append(page.extract_text() or "")
    return "\n".join(out)


def _ocr_image(path: Path) -> str:
    img, tess = _ocr_deps()
    return tess.image_to_string(img.open(str(path)))


def _ocr_pdf(path: Path) -> str:
    """Render each page and OCR it. ponytail: 300dpi full-page OCR, fine for a
    handful of pages; batch/queue it if you throw hundreds at it."""
    import pdfplumber

    img, tess = _ocr_deps()
    out = []
    with pdfplumber.open(str(path)) as pdf:
        for page in pdf.pages:
            pil = page.to_image(resolution=300).original
            out.append(tess.image_to_string(pil))
    return "\n".join(out)


def _ocr_deps():
    try:
        from PIL import Image
        import pytesseract
    except ImportError as e:  # pragma: no cover - env guard
        raise ExtractError(
            "OCR needs Pillow + pytesseract (and the tesseract binary): "
            "pip install pillow pytesseract && sudo apt install tesseract-ocr"
        ) from e
    return Image, pytesseract
