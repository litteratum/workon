.PHONY: venv
venv:
	poetry install

.PHONY: clean_coverage
clean_coverage:
	rm -rf .coverage htmlcov

.PHONY: clean
clean: clean_coverage
	rm -rf .venv build _build dist *.egg-info .mypy_cache
	find . -type f -name '*.py[co]' -delete -o -type d -name __pycache__ -delete
	py3clean . -v

.PHONY: test
test:
	poetry run pytest -svvv tests

.PHONY: coverage
coverage:
	poetry run pytest --cov-report html --cov=git_workon tests/

.PHONY: build
build:
	poetry build

.PHONY: publish
publish:
	poetry publish
