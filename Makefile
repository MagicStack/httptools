compile:
	cython httptools/parser/parser.pyx
	python3 setup.py build_ext --inplace


release: compile
	python3 setup.py sdist upload
