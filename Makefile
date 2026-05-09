PYTHON := venv/bin/python
PIP := venv/bin/pip

setup:
	python3 -m venv venv
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

run:
	$(PYTHON) run_desktop.py

cli:
	$(PYTHON) main.py $(VIDEO)
