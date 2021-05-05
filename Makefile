VENV=venv/linux
VENV_PIP=$(VENV)/bin/python -m pip


$(VENV):
	python3 -m venv $(VENV)
	$(VENV_PIP) install -e .

venv: $(VENV)

clean:
	rm -rf venv build dist *.egg-info .mypy_cache
	find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete
	py3clean . -v

install:
	python3 setup.py install --user

test_req:
	$(VENV_PIP) install pytest

test: venv test_req
	$(VENV_PIP) install pytest
	$(VENV)/bin/pytest -svvv tests/unit

test_integration: venv test_req
	$(VENV)/bin/pytest -svvv tests/integration

test_all: venv test_req
	$(VENV)/bin/pytest -svvv tests
