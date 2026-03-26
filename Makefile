PYTHON ?= python3

.PHONY: install run check clean

install:
	$(PYTHON) -m pip install -r requirements.txt

run:
	$(PYTHON) run_both.py

check:
	$(PYTHON) -m compileall shivu moto resolve_peer.py

clean:
	find . -type d -name "__pycache__" -prune -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
