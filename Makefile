PYTHON ?= python

.PHONY: lint
lint: lint-isort lint-flake8

.PHONY: lint-isort
lint-isort:
	isort --check-only --quiet --diff --recursive .

.PHONY: lint-flake8
lint-flake8:
	flake8 .

.PHONY: format
format: format-isort

.PHONY: format-isort
format-isort:
	isort --quiet --diff --recursive .

.PHONY: test
test:
	pytest

.PHONY: coverage
coverage:
	pytest --cov

.PHONY: docs
docs:
	$(MAKE) -C docs html

.PHONY: build
build:
	$(PYTHON) setup.py build

.PHONY: dist
dist:
	$(PYTHON) setup.py sdist bdist_wheel
