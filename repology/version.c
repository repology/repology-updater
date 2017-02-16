/*
 * Copyright (C) 2017 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

#include <Python.h>

#include <stdio.h>
#include <stdint.h>

#define VERCOMP_MAX ((LONG_MAX - 9) / 10)

#define MY_MIN(a, b) ((a) < (b) ? (a) : (b))
#define MY_MAX(a, b) ((a) > (b) ? (a) : (b))

static int IsVersionChar(char c) {
	return (c >= '0' && c <= '9') || (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z');
}

static long ParseNumber(const char** str) {
	const char *cur = *str;
	long number = 0;
	while (*cur >= '0' && *cur <= '9') {
		number = number * 10 + (*cur - '0');
		if (number > VERCOMP_MAX)
			number = VERCOMP_MAX;
		cur++;
	}

	if (cur == *str)
		return -1;

	*str = cur;
	return number;
}

static long ParseAlpha(const char** str) {
	char start = **str;

	const char *cur = *str;

	while ((*cur >= 'a' && *cur <= 'z') || (*cur >= 'A' && *cur <= 'Z'))
		cur++;

	if (cur == *str)
		return 0;

	*str = cur;

	if (start >= 'A' && start <= 'Z')
		return start - 'A' + 'a'; // lowercase
	else
		return start;
}

static size_t GetNextVersionComponent(const char** str, long* target) {
	// skip separators
	while (**str != '\0' && !IsVersionChar(**str))
		++*str;

	// EOL, generate empty component
	if (**str == '\0') {
		*(target++) = 0;
		*(target++) = 0;
		*(target++) = -1;
		return 3;
	}

	const char *end = *str;
	while (IsVersionChar(*end))
		end++;

	// parse component from string [str; end)
	long number = ParseNumber(str);
	long alpha = ParseAlpha(str);
	long extranumber = ParseNumber(str);

	// skip remaining alphanumeric part
	while (IsVersionChar(**str))
		++*str;

	// split part with two numbers
	if (number != -1 && extranumber != -1) {
		*(target++) = number;
		*(target++) = 0;
		*(target++) = -1;
		*(target++) = -1;
		*(target++) = alpha;
		*(target++) = extranumber;
		return 6;
	} else {
		*(target++) = number;
		*(target++) = alpha;
		*(target++) = extranumber;
		return 3;
	}
}

static PyObject* VersionCompare(PyObject *self, PyObject *args) {
	const char *v1;
	const char *v2;

	if (!PyArg_ParseTuple(args, "ss", &v1, &v2))
		return NULL;

	const char *v1_end = v1 + strlen(v1);
	const char *v2_end = v2 + strlen(v1);

	long v1_comps[6];
	long v2_comps[6];
	size_t v1_len = 0;
	size_t v2_len = 0;
	while (*v1 != '\0' || *v2 != '\0' || v1_len || v2_len) {
		if (v1_len == 0)
			v1_len = GetNextVersionComponent(&v1, v1_comps);
		if (v2_len == 0)
			v2_len = GetNextVersionComponent(&v2, v2_comps);

		const size_t shift = MY_MIN(v1_len, v2_len);
		for (size_t i = 0; i < shift; i++) {
			if (v1_comps[i] < v2_comps[i])
				return PyLong_FromLong(-1);
			if (v1_comps[i] > v2_comps[i])
				return PyLong_FromLong(1);
		}

		if (v1_len != v2_len) {
			for (size_t i = 0; i < shift; i++) {
				v1_comps[i] = v1_comps[i+shift];
				v2_comps[i] = v2_comps[i+shift];
			}
		}

		v1_len -= shift;
		v2_len -= shift;
	}

	return PyLong_FromLong(0);
}

static PyMethodDef module_methods[] = {
	{"VersionCompare", (PyCFunction)VersionCompare, METH_VARARGS, ""},
	{NULL, NULL, 0, NULL}
};

static struct PyModuleDef module_definition = {
	PyModuleDef_HEAD_INIT,
	"repology.version",
	NULL,
	-1,
	module_methods,
	NULL,
	NULL,
	NULL,
	NULL
};

PyMODINIT_FUNC PyInit_version(void) {
	return PyModule_Create(&module_definition);
}
