FLAKE8?=	flake8
MYPY?=		mypy

STATICDIR=	repologyapp/static

all: gzip-static

gzip-static:
	gzip -9 -f -k -v ${STATICDIR}/*.css ${STATICDIR}/*.js ${STATICDIR}/*.ico ${STATICDIR}/*.svg

clean:
	rm -f ${STATICDIR}/*.gz

lint:: check test flake8 mypy

test::
	python3 -m unittest discover

full-test::
	env REPOLOGY_CONFIG=./repology-test.conf.default ./repology-update.py -ippd
	env REPOLOGY_CONFIG=./repology-test.conf.default python3 -m unittest discover

flake8:
	${FLAKE8} --count --application-import-names=repology *.py repology repologyapp

mypy:
	${MYPY} *.py repology repologyapp
	${MYPY} repology/fetchers/fetchers
	${MYPY} repology/parsers/parsers
	${MYPY} repologyapp/views

check:
	python3 repology-schemacheck.py -s repos $$(find repos.d -name "*.yaml")
