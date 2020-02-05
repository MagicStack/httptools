.PHONY: compile release test distclean clean


PYTHON ?= python3
ROOT = $(dir $(realpath $(firstword $(MAKEFILE_LIST))))


compile:
	python3 setup.py build_ext --inplace


release: compile test
	python3 setup.py sdist upload


test:
	python3 setup.py test

clean:
	find $(ROOT)/httptools/parser -name '*.c' | xargs rm -f
	find $(ROOT)/httptools/parser -name '*.html' | xargs rm -f

distclean:
	git --git-dir="$(ROOT)/vendor/http-parser/.git" clean -dfx
	find $(ROOT)/httptools/parser -name '*.c' | xargs rm -f
	find $(ROOT)/httptools/parser -name '*.html' | xargs rm -f


testinstalled:
	cd /tmp && $(PYTHON) $(ROOT)/tests/__init__.py