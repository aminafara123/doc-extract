"""End-to-end with the LLM mocked. No network, no tesseract."""
import csv

import pytest

from doc_extract import llm, pipeline


@pytest.fixture
def mock_chat(monkeypatch):
    """Make llm.chat return a chosen JSON string instead of calling a model."""
    def _set(reply):
        monkeypatch.setattr(llm, "chat", lambda *a, **k: reply)
    return _set


def test_extract_clean(mock_chat, clean_json):
    mock_chat(clean_json)
    inv, confidence, warnings = pipeline.extract_invoice("irrelevant text")
    assert inv.vendor == "ACME Cloud Services, Inc."
    assert inv.date == "2024-03-15"  # normalized
    assert confidence == "high"
    assert warnings == []


def test_extract_mismatch_flags(mock_chat, mismatch_json):
    mock_chat(mismatch_json)
    inv, confidence, warnings = pipeline.extract_invoice("irrelevant")
    assert confidence == "low"
    assert any("total" in w for w in warnings)


def test_process_file_writes_json(mock_chat, clean_json, tmp_path):
    mock_chat(clean_json)
    doc = tmp_path / "some-invoice.txt"
    doc.write_text("ACME invoice text", encoding="utf-8")
    out = tmp_path / "out"

    result = pipeline.process_file(doc, out)

    assert result["ai_generated"] is True
    assert result["confidence"] == "high"
    written = out / "some-invoice.json"
    assert written.exists()
    assert "notice" in result and "review" in result["notice"].lower()


def test_process_file_survives_llm_failure(monkeypatch, tmp_path):
    def boom(*a, **k):
        raise llm.LLMError("no model running")
    monkeypatch.setattr(llm, "chat", boom)

    doc = tmp_path / "bad.txt"
    doc.write_text("whatever", encoding="utf-8")
    result = pipeline.process_file(doc, tmp_path / "out")

    assert "error" in result
    assert "LLMError" in result["error"]  # recorded, not raised


def test_csv_aggregation(mock_chat, clean_json, mismatch_json, tmp_path, monkeypatch):
    out = tmp_path / "out"
    # two documents -> two rows + header
    monkeypatch.setattr(llm, "chat", lambda *a, **k: clean_json)
    r1 = pipeline.process_file(_mk(tmp_path, "a.txt"), out)
    monkeypatch.setattr(llm, "chat", lambda *a, **k: mismatch_json)
    r2 = pipeline.process_file(_mk(tmp_path, "b.txt"), out)

    csv_path = pipeline.write_csv([r1, r2], out / "invoices.csv")
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8")))

    assert len(rows) == 2
    assert rows[0]["vendor"] == "ACME Cloud Services, Inc."
    assert rows[0]["confidence"] == "high"
    assert rows[1]["confidence"] == "low"
    assert rows[1]["warnings"]  # mismatch warning carried into the CSV
    assert int(rows[0]["line_items"]) == 4


def test_process_path_on_dir(mock_chat, clean_json, tmp_path):
    mock_chat(clean_json)
    (tmp_path / "x.txt").write_text("t", encoding="utf-8")
    (tmp_path / "y.txt").write_text("t", encoding="utf-8")
    (tmp_path / "ignore.md").write_text("not a doc", encoding="utf-8")
    out = tmp_path / "out"

    results = pipeline.process_path(tmp_path, out_dir=out)

    assert len(results) == 2  # .md skipped
    assert (out / "invoices.csv").exists()


def _mk(dir_, name):
    p = dir_ / name
    p.write_text("doc text", encoding="utf-8")
    return p
