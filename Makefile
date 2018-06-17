FLAKE8?=	flake8

STATICDIR=	repologyapp/static

all: gzip-static

gzip-static:
	gzip -9 -f -k -v ${STATICDIR}/*.css ${STATICDIR}/*.js ${STATICDIR}/*.ico ${STATICDIR}/*.svg

clean:
	rm -f helpers/rpmcat/rpmcat
	rm -f ${STATICDIR}/*.gz
	rm -rf build
	rm -f repology/version.so

test::
	python3 -m unittest discover

profile-dump::
	python3 -m cProfile -o _profile ./repology-dump.py --stream >/dev/null 2>&1
	python3 -c 'import pstats; stats = pstats.Stats("_profile"); stats.sort_stats("time"); stats.print_stats()' | less

profile-reparse::
	python3 -m cProfile -o _profile ./repology-update.py -P >/dev/null 2>&1
	python3 -c 'import pstats; stats = pstats.Stats("_profile"); stats.sort_stats("time"); stats.print_stats()' | less

flake8:
	${FLAKE8} --ignore=E501,F405,F403,E265,D10,E722,N802 --application-import-names=repology *.py repology repologyapp test

flake8-all:
	${FLAKE8} --application-import-names=repology *.py repology repologyapp test

check:
	python3 repology-schemacheck.py -s repos $$(find repos.d -name "*.yaml")
