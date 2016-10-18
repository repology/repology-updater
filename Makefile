CC?=		gcc
CFLAGS+=	-Wall -Wextra

CPPFLAGS+=	`pkg-config --cflags rpm`
LDFLAGS+=	`pkg-config --libs rpm`

all: cutils/rpmcat

cutils/rpmcat: cutils/rpmcat.c
	${CC} cutils/rpmcat.c -o cutils/rpmcat ${CFLAGS} ${CPPFLAGS} ${LDFLAGS}

clean:
	rm cutils/rpmcat

test::
	python3 -m unittest discover

check:
	kwalify -lf schemas/rules.yaml rules.yaml | tee kwalify.log
	@if grep -q INVALID kwalify.log; then \
		echo "Validation failed"; \
		rm -f kwalify.log; \
		false; \
	else \
		rm -f kwalify.log; \
	fi
