.PHONY: compile release test distclean


compile:
	python3 setup.py build_ext --inplace


release: compile test
	python3 setup.py sdist upload


test:
	python3 setup.py test


distclean:
	git --git-dir="./vendor/http-parser/.git" clean -dfx
	find ./httptools/parser -name '*.c' | xargs rm -f
	find ./httptools/parser -name '*.html' | xargs rm -f
