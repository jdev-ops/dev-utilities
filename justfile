set shell := ["sh", "-c"]
set allow-duplicate-recipes
set positional-arguments
set dotenv-load
set export

default: req

shfmt:
	shfmt -i 2 -l -w bin/*

pyfmt:
	black lib/
	black setup.py

req:
	pip install -r requirements/dev.txt
