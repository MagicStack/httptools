.PHONY: compile release test distclean clean


PYTHON ?= python3
ROOT = $(dir $(realpath $(firstword $(MAKEFILE_LIST))))
UV := $(shell command -v uv 2> /dev/null)
ifdef UV
	PYTHON := uv run
	PIP := uv pip
else
	PIP := pip
endif

compile:
	$(PIP) install -e .

test: compile
	$(PYTHON) -m unittest -v

clean:
	find $(ROOT)/httptools/parser -name '*.c' | xargs rm -f
	find $(ROOT)/httptools/parser -name '*.so' | xargs rm -f
	find $(ROOT)/httptools/parser -name '*.html' | xargs rm -f
	rm -rf build

distclean: clean
	git --git-dir="$(ROOT)/vendor/http-parser/.git" clean -dfx
	git --git-dir="$(ROOT)/vendor/llhttp/.git" clean -dfx
