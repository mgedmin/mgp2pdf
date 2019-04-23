PYTHON := python

FILE_WITH_VERSION := setup.py
FILE_WITH_CHANGELOG := CHANGES.rst

DISTCHECK_DIFF_OPTS = $(DISTCHECK_DIFF_DEFAULT_OPTS) -x samples -x 'samples/*'


.PHONY: all
all:
	@echo "Nothing to do"


.PHONY: test check
test check:
	tox -p auto

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
