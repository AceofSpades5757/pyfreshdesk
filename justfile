PYTHON := if os_family() == "windows" {"py"} else {"python3"}
VENV := ".venv"
VENV_BIN := VENV + if os_family() == "windows" {"/Scripts"} else {"/bin"}
VENV_PYTHON := VENV_BIN + "/python"
VENV_PIP := VENV_PYTHON + " -m pip"

_default: help


help:
    @just --list

all: venv


venv:
    @[ -d {{VENV}} ] || just _venv

alias fmt := format
format: venv
	@echo "Running CI pipline for formatting."
	{{VENV_BIN}}/pre-commit run --all-files

format-update: venv
    @echo "Updating pre-commit hooks."
    {{VENV_BIN}}/pre-commit autoupdate

mostlyclean:
    # build files
    -fd --no-ignore --glob *.egg-info --exec rm -rf
    # log files
    -fd --no-ignore --glob *.log --exec rm -rf
    # cache files
    -fd --no-ignore --glob __pycache__ --exec rm -rf

clean: mostlyclean
    # virtual env dirs
    rm -rf {{VENV}}
    # Build and Dist dirs
    rm -rf ./build
    rm -rf ./dist

build: venv
    {{VENV_PYTHON}} -m build

publish: build
    {{VENV_PYTHON}} -m twine upload dist/*


_venv:
    {{PYTHON}} -m pip install --upgrade pip
    {{PYTHON}} -m pip install --upgrade virtualenv
    {{PYTHON}} -m virtualenv {{VENV}}
    {{VENV_PIP}} install --upgrade pip
    {{VENV_PIP}} install --editable .[dev]
