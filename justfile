set shell := ["sh", "-c"]
set allow-duplicate-recipes
set positional-arguments
set dotenv-load
set export

fmt-sh:
    # Format shell scripts in the bin directory
    shfmt -i 2 -l -w bin/*

fmt-py:
    ruff check --select I --fix
    ruff format

publish:
    hatch build --clean
    hatch publish -r http://localhost:3141/testuser/dev

build:
    hatch build --clean
