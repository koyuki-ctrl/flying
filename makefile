PYTHON_VERSION = 3
REQUIREMENTS = requirements.txt
VENV_DIR = .venv
MAP ?= maps/easy/01_linear_path.txt
VENV_PYTHON = $(VENV_DIR)/bin/python
VENV_PIP = $(VENV_DIR)/bin/pip

$(VENV_DIR): $(REQUIREMENTS)
	python$(PYTHON_VERSION) -m venv $(VENV_DIR)
	$(VENV_PIP) install --upgrade pip
	$(VENV_PIP) install -r $(REQUIREMENTS)

install: $(VENV_DIR)

run: install
	$(VENV_PYTHON) main.py $(MAP)

debug: install
	$(VENV_PYTHON) -m pdb main.py $(MAP)

clean:
	rm -rf $(VENV_DIR) __pycache__ *.pyc .mypy_cache .pytest_cache

re: clean $(VENV_DIR)

lint: install
	$(VENV_PYTHON) -m flake8 --exclude=.venv,__pycache__,.mypy_cache
	$(VENV_PYTHON) -m mypy --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs .

lint-strict: install
	$(VENV_PYTHON) -m flake8 --exclude=.venv,__pycache__,.mypy_cache
	$(VENV_PYTHON) -m mypy --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs --strict .

freeze:
	$(VENV_PYTHON) -m pip freeze > $(REQUIREMENTS)

.PHONY: install run debug clean lint lint-strict freeze re
