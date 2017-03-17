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
#include <libversion/compare.h>

static PyObject* VersionCompare(PyObject *self, PyObject *args) {
	(void)self; // (unused)

	const char *v1;
	const char *v2;

	if (!PyArg_ParseTuple(args, "ss", &v1, &v2))
		return NULL;

	return PyLong_FromLong(version_compare_simple(v1, v2));
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
