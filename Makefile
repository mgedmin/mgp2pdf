.PHONY: all
all:
	@echo "Nothing to do"

.PHONY: test
test:                   ##: run tests
	tox -p auto

.PHONY: coverage
coverage:               ##: measure test coverage
	tox -e coverage

.PHONY: smoketest-coverage
smoketest-coverage:     ##: measure coverage of smoke tests
	tox -e smoketest-coverage


DISTCHECK_DIFF_OPTS = $(DISTCHECK_DIFF_DEFAULT_OPTS) -x samples -x 'samples/*'
include release.mk
