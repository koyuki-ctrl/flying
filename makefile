PYTHON_VERSION = 3.12
PACKAGE_manager = pip
REQUIREMENTS = requirements.txt
VENV_DIR = .venv

install:
	python$(PYTHON_VERSION) -m venv $(VENV_DIR)
	source $(VENV_DIR)/bin/activate && $(PACKAGE_manager) install -r $(REQUIREMENTS)

run:
	python$(PYTHON_VERSION) main.py

debug:
	python$(PYTHON_VERSION) -m pdb main.py

clean:
	rm -rf $(VENV_DIR) __pycache__ *.pyc .mypy_cache

lint:
	flake8 --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs 
	mypy --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs .

lint-strict:
	flake8 --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs 
	mypy --warn-return-any --warn-unused-ignores --ignore-missing-imports --disallow-untyped-defs --check-untyped-defs --strict .

freeze:
	pip freeze > $(REQUIREMENTS)

.PHONY: install run debug clean lint lint-strict freeze