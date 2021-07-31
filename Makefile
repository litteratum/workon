VENV=venv/linux
VENV_PIP=$(VENV)/bin/python -m pip


$(VENV):
	python3 -m venv $(VENV)
	$(VENV_PIP) install -e .

venv: $(VENV)

clean_coverage:
	rm -rf .coverage htmlcov

clean: clean_coverage
	rm -rf venv build dist *.egg-info .mypy_cache
	find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete
	py3clean . -v

install:
	/usr/bin/python3 -m pip install .

test_req: venv
	$(VENV_PIP) install pytest pytest-cov

test: test_req
	$(VENV)/bin/pytest -svvv tests/unit

test_integration: test_req
	$(VENV)/bin/pytest -svvv tests/integration

test_all: test_req
	$(VENV)/bin/pytest -svvv tests

coverage: test_req
	pytest --cov-report html --cov=workon tests/
