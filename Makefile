CC?=		gcc
CFLAGS+=	-Wall -Wextra

CPPFLAGS+=	`pkg-config --cflags rpm`
LDFLAGS+=	`pkg-config --libs rpm`

all: cutils/rpmcat

cutils/rpmcat: cutils/rpmcat.c
	${CC} cutils/rpmcat.c -o cutils/rpmcat ${CFLAGS} ${CPPFLAGS} ${LDFLAGS}

clean:
	rm cutils/rpmcat

check:
	kwalify -lf schemas/rules.yaml rules.yaml
