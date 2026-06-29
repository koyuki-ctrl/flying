PYTHON_VERSION = 3.13
PACKAGE_manager = pip
REQUIREMENTS = requirements.txt
VENV_DIR = .venv
MAP ?= maps/easy/01_linear_path.txt

install:
	python$(PYTHON_VERSION) -m venv $(VENV_DIR)
	. $(VENV_DIR)/bin/activate && $(PACKAGE_manager) install -r $(REQUIREMENTS)

run:
	python$(PYTHON_VERSION) main.py $(MAP)

debug:
	python$(PYTHON_VERSION) -m pdb main.py

clean:
	rm -rf $(VENV_DIR) __pycache__ *.pyc .mypy_cache

lint:
	python$(PYTHON_VERSION) -m flake8 --exclude=.venv,__pycache__,.mypy_cache
	python$(PYTHON_VERSION) -m mypy --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs .

lint-strict:
	python$(PYTHON_VERSION) -m flake8 --exclude=.venv,__pycache__,.mypy_cache
	python$(PYTHON_VERSION) -m mypy --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs --strict .

freeze:
	python$(PYTHON_VERSION) -m pip freeze > $(REQUIREMENTS)

.PHONY: install run debug clean lint lint-strict freeze