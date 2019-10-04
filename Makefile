FLAKE8?=	flake8
MYPY?=		mypy

lint:: check test flake8 mypy

test::
	python3 -m unittest discover

full-test::
	env REPOLOGY_CONFIG=./repology-test.conf.default ./repology-update.py -ippd
	env REPOLOGY_CONFIG=./repology-test.conf.default python3 -m unittest discover

flake8:
	${FLAKE8} --application-import-names=repology *.py repology

mypy:
	${MYPY} *.py repology
	${MYPY} repology/fetchers/fetchers
	${MYPY} repology/parsers/parsers

check:
	python3 repology-schemacheck.py -s repos $$(find repos.d -name "*.yaml")
