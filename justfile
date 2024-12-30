set shell := ["sh", "-c"]
set allow-duplicate-recipes
set positional-arguments
set dotenv-load
set export

shfmt:
	shfmt -i 2 -l -w bin/*

pyfmt:
	black src/

publish:
    hatch build --clean
    hatch publish -r http://localhost:3141/testuser/dev

build:
    hatch build --clean
