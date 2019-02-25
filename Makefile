.PHONY: compile release test distclean


compile:
	cython httptools/parser/parser.pyx
	python3 setup.py build_ext --inplace


release: compile test
	python3 setup.py sdist upload


test:
	python3 -m unittest discover -s tests -v


distclean:
	git --git-dir="./vendor/http-parser/.git" clean -dfx
	find ./httptools/parser -name '*.c' | xargs rm
	find ./httptools/parser -name '*.html' | xargs rm
