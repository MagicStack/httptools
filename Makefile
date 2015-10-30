.PHONY: compile release test


compile:
	cython httptools/parser/parser.pyx
	python3 setup.py build_ext --inplace


release: compile test
	python3 setup.py sdist upload


test:
	python3 -m unittest discover -s tests -v
