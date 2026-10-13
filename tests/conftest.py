import json
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


def load(name):
    return (FIXTURES / name).read_text(encoding="utf-8")


@pytest.fixture
def clean_json():
    return load("clean_invoice.json")


@pytest.fixture
def mismatch_json():
    return load("mismatch_invoice.json")


@pytest.fixture
def clean_data():
    return json.loads(load("clean_invoice.json"))


@pytest.fixture
def mismatch_data():
    return json.loads(load("mismatch_invoice.json"))
