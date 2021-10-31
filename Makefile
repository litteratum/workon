PIP_VER=21.2.4
SETUPTOOLS_VER=58.1.0

VENV=venv/linux
VENV_PIP=$(VENV)/bin/python -m pip
BUILD_DIR=_build


$(VENV):
	python3 -m venv $(VENV)
	$(VENV_PIP) install pip==$(PIP_VER)
	$(VENV_PIP) install setuptools==$(SETUPTOOLS_VER)
	$(VENV_PIP) install -e .

venv: $(VENV)

build:
	python3 -m venv $(BUILD_DIR)
	$(BUILD_DIR)/bin/pip install pip==$(PIP_VER)
	$(BUILD_DIR)/bin/pip install setuptools==$(SETUPTOOLS_VER)
	$(BUILD_DIR)/bin/pip install -U twine
	$(BUILD_DIR)/bin/python setup.py sdist

publish: build
	$(BUILD_DIR)/bin/python -m twine upload dist/*

clean_coverage:
	rm -rf .coverage htmlcov

clean: clean_coverage
	rm -rf venv build _build dist *.egg-info .mypy_cache
	find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete
	py3clean . -v

test_req: venv
	$(VENV_PIP) install pytest pytest-cov

test: test_req
	$(VENV)/bin/pytest -svvv tests

coverage: test_req
	$(VENV)/bin/pytest --cov-report html --cov=git_workon tests/

.PHONY: clean_coverage clean test_req test coverage build publish
