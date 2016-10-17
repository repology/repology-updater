/*
 * Copyright (C) 2016 Dmitry Marakasov <amdmi3@amdmi3.ru>
 *
 * This file is part of repology
 *
 * repology is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * repology is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 *
 * You should have received a copy of the GNU General Public License
 * along with repology.  If not, see <http://www.gnu.org/licenses/>.
 */

#include <stdio.h>
#include <rpm/header.h>

int main(int argc, char** argv) {
	if (argc != 2) {
		fprintf(stderr, "Usage: %s <file>\n", argv[0]);
		return 1;
	}

	FD_t rpmfile = Fopen(argv[1], "r.ufdio");
	if (Ferror(rpmfile)) {
		fprintf(stderr, "FATAL: cannot open file: %s\n", Fstrerror(rpmfile));
		return 1;
	}

	Header header;
	while ((header = headerRead(rpmfile, HEADER_MAGIC_YES)) != NULL) {
		const char *errmsg = "unknown error";
		char *str = headerFormat(header, "%{name}|%{version}|%{packager}|%{group}|%{summary}\n", &errmsg);

		if (str != NULL) {
			fputs(str, stdout);
			free(str);
		} else {
			fprintf(stderr, "FATAL: cannot parse file: %s\n", errmsg);
			Fclose(rpmfile);
			return 1;
		}
		headerFree(header);
    }

	Fclose(rpmfile);

	return 0;
}
