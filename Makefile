PYTHON := python

FILE_WITH_VERSION := setup.py
FILE_WITH_CHANGELOG := CHANGES.rst


.PHONY: all
all:
	@echo "Nothing to do"


.PHONY: test check
test check:
	detox

.PHONY: coverage
coverage:
	tox -e coverage

.PHONY: smoketest-coverage
smoketest-coverage:
	test -x bin/pip || virtualenv .
	test -x bin/coverage || bin/pip install coverage
	test -x bin/mgp2pdf || bin/pip install -e .
	tox -e coverage
	bin/coverage run -a --source=mgp2pdf.py -m mgp2pdf --unsafe -o /tmp/ samples/*/*.mgp -v > /dev/null
	bin/coverage report


include release.mk
