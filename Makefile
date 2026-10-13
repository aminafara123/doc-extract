.PHONY: install test run samples clean
VENV := .venv
PY := $(VENV)/bin/python

install:
	python3 -m venv $(VENV)
	$(PY) -m pip install -U pip
	$(PY) -m pip install -r requirements.txt

samples:        ## regenerate the sample PDFs (reportlab)
	$(PY) sample/_gen_samples.py

test:           ## offline, no network, no tesseract
	$(PY) -m pytest -q

run:            ## extract everything in sample/ -> out/
	$(PY) -m doc_extract sample/

clean:
	rm -rf out .pytest_cache **/__pycache__ __pycache__
