.PHONY: compile release test


compile:
	cython httptools/parser/parser.pyx
	python setup.py build_ext --inplace


release: compile test
	python setup.py sdist upload

build: compile
	python setup.py bdist_wheel

test:
	python -m unittest discover -s tests -v
