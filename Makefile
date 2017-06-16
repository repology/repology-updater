FLAKE8?=	flake8

CC?=		gcc
CFLAGS?=	-O3
CFLAGS+=	-Wall -Wextra

CPPFLAGS+=	`pkg-config --cflags rpm`
LDFLAGS+=	`pkg-config --libs rpm`

all: helpers/rpmcat/rpmcat repology/version.so gzip-static

repology/version.so: build/repology/version.so
	cp build/repology/version*.so repology/version.so

build/repology/version.so: repology/version.c
	env CFLAGS="${CFLAGS}" python3 setup.py build --build-lib build build

gzip-static:
	gzip -9 -f -k -v static/*.css static/*.js static/*.ico static/*.svg

helpers/rpmcat/rpmcat: helpers/rpmcat/rpmcat.c
	${CC} helpers/rpmcat/rpmcat.c -o helpers/rpmcat/rpmcat ${CFLAGS} ${CPPFLAGS} ${LDFLAGS}

clean:
	rm -f helpers/rpmcat/rpmcat
	rm -f static/*.gz
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
	${FLAKE8} --ignore=E501,F401,F405,F403,E265,D10 --application-import-names=repology *.py repology test

flake8-all:
	${FLAKE8} --application-import-names=repology *.py repology test

check:
	python3 repology-schemacheck.py -s rules $$(find rules.d -name "*.yaml")
	python3 repology-schemacheck.py -s repos $$(find repos.d -name "*.yaml")
