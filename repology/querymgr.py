# Copyright (C) 2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
#
# This file is part of repology
#
# repology is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# repology is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with repology.  If not, see <http://www.gnu.org/licenses/>.

# mypy: no-disallow-untyped-defs
# mypy: no-disallow-untyped-calls
# mypy: no-warn-return-any

import functools
import os
import re
from typing import Any, Callable, ClassVar, Dict, List

import jinja2

import psycopg2.extras

from repology.package import Package


__all__ = ['QueryLoadingError', 'QueryMetadataParsingError', 'QueryManager']


class QueryMetadataParsingError(RuntimeError):
    pass


class QueryLoadingError(RuntimeError):
    pass


class QueryMetadata:
    RET_NONE: ClassVar[int] = 0
    RET_SINGLE_VALUE: ClassVar[int] = 1
    RET_SINGLE_DICT: ClassVar[int] = 2
    RET_SINGLE_TUPLE: ClassVar[int] = 3
    RET_ARRAY_OF_VALUES: ClassVar[int] = 4
    RET_ARRAY_OF_DICTS: ClassVar[int] = 5
    RET_ARRAY_OF_TUPLES: ClassVar[int] = 6
    RET_ARRAY_OF_PACKAGES: ClassVar[int] = 7
    RET_DICT_AS_DICTS: ClassVar[int] = 8

    ARGSMODE_NORMAL: ClassVar[int] = 0
    ARGSMODE_MANY_VALUES: ClassVar[int] = 1
    ARGSMODE_MANY_OBJECTS: ClassVar[int] = 2
    ARGSMODE_MANY_DICTS: ClassVar[int] = 3
    ARGSMODE_MANY_TUPLES: ClassVar[int] = 4

    name: str
    query: str
    template: jinja2.Template
    args: List[Any]
    argdefaults: Dict[str, Any]
    rettype: int
    argsmode: int

    def __init__(self, name: str, query: str) -> None:
        self.name = name
        self.query = query
        self.template = jinja2.Template(query)
        self.args = []
        self.argdefaults = {}
        self.rettype = QueryMetadata.RET_NONE
        self.argsmode = QueryMetadata.ARGSMODE_NORMAL

        for line in query.split('\n'):
            match = re.fullmatch('\\s*--\\s*(@.*?)\\s*', line)
            if match:
                self._parse_annotation(match.group(1))

    def _parse_annotation(self, string: str) -> None:
        """Parse query metadata from the string definition.

        Input examples:

            - funcname()
            Takes no arguments, returns nothing

            - funcname(arg)
            Takes single argument, returns nothing

            - funcname(arg1, arg2=True, arg3=False, arg4=123, arg5="str") -> scalar
            Takes 5 arguments, some with default values, returns single value
        """
        annkey, annvalue = string.split(None, 1)

        if annkey == '@param':
            self._parse_argument(annvalue)
        elif annkey == '@returns':
            self._parse_return_type(annvalue)

    def _parse_argument(self, string: str) -> None:
        if string == 'many values':
            self.argsmode = QueryMetadata.ARGSMODE_MANY_VALUES
            return

        if string == 'many objects':
            self.argsmode = QueryMetadata.ARGSMODE_MANY_OBJECTS
            return

        if string == 'many dicts':
            self.argsmode = QueryMetadata.ARGSMODE_MANY_DICTS
            return

        if string == 'many tuples':
            self.argsmode = QueryMetadata.ARGSMODE_MANY_TUPLES
            return

        argname, *rest = [s.strip() for s in string.split('=', 1)]

        argdefault = rest[0] if rest else None

        if not argname:
            raise QueryMetadataParsingError('Cannot parse query metadata "{}": bad arguments'.format(string))

        self.args.append(argname)

        if argdefault is None:
            pass
        elif argdefault.isdecimal():
            self.argdefaults[argname] = int(argdefault)
        elif argdefault.startswith("'"):
            self.argdefaults[argname] = argdefault.strip("'")
        elif argdefault.startswith('"'):
            self.argdefaults[argname] = argdefault.strip('"')
        elif argdefault == 'True':
            self.argdefaults[argname] = True
        elif argdefault == 'False':
            self.argdefaults[argname] = False
        elif argdefault == 'None':
            self.argdefaults[argname] = None
        else:
            raise QueryMetadataParsingError('Cannot parse query metadata "{}": bad default value for argument "{}"'.format(string, argname))

    def _parse_return_type(self, string: str) -> None:
        if not string:
            self.rettype = QueryMetadata.RET_NONE
        elif string == 'single value':
            self.rettype = QueryMetadata.RET_SINGLE_VALUE
        elif string == 'single dict':
            self.rettype = QueryMetadata.RET_SINGLE_DICT
        elif string == 'single tuple':
            self.rettype = QueryMetadata.RET_SINGLE_TUPLE
        elif string == 'array of values':
            self.rettype = QueryMetadata.RET_ARRAY_OF_VALUES
        elif string == 'array of dicts':
            self.rettype = QueryMetadata.RET_ARRAY_OF_DICTS
        elif string == 'array of tuples':
            self.rettype = QueryMetadata.RET_ARRAY_OF_TUPLES
        elif string == 'array of packages':
            self.rettype = QueryMetadata.RET_ARRAY_OF_PACKAGES
        elif string == 'dict of dicts':
            self.rettype = QueryMetadata.RET_DICT_AS_DICTS
        else:
            raise QueryMetadataParsingError('Cannot parse query metadata "{}": bad return specification'.format(string))


class QueryManager:
    _queries: Dict[str, Callable[..., Any]]

    def __init__(self, queriesdir: str) -> None:
        self._queries = {}

        for root, dirs, files in os.walk(queriesdir):
            for filename in files:
                if not filename.endswith('.sql'):
                    continue

                try:
                    with open(os.path.join(root, filename), 'r', encoding='utf-8') as sqlfile:
                        self._register_query(QueryMetadata(
                            filename[:-4],
                            sqlfile.read()
                        ))
                except QueryMetadataParsingError as e:
                    raise QueryLoadingError('Cannot load SQL query from {}: {}'.format(filename, str(e)))

    def _register_query(self, query: QueryMetadata) -> None:
        def adapt_dict_argument(data):
            if isinstance(data, dict):
                return psycopg2.extras.Json(data)
            elif isinstance(data, list) and data and isinstance(data[0], dict):
                return psycopg2.extras.Json(data)
            return data

        def adapt_dict_arguments(data):
            return {
                key: adapt_dict_argument(value)
                for key, value in data.items()
            }

        def prepare_arguments_for_query(args, kwargs):
            if query.argsmode == QueryMetadata.ARGSMODE_MANY_VALUES:
                return [[value] for value in args[0]]

            if query.argsmode == QueryMetadata.ARGSMODE_MANY_OBJECTS:
                return [adapt_dict_arguments(package.__dict__) for package in args[0]]

            if query.argsmode == QueryMetadata.ARGSMODE_MANY_DICTS:
                return [adapt_dict_arguments(item) for item in args[0]]

            if query.argsmode == QueryMetadata.ARGSMODE_MANY_TUPLES:
                return args[0]

            assert(query.argsmode == QueryMetadata.ARGSMODE_NORMAL)

            args_for_query = {}
            for narg, argname in enumerate(query.args):
                if narg < len(args):
                    args_for_query[argname] = args[narg]
                elif argname in kwargs:
                    args_for_query[argname] = kwargs[argname]
                elif argname in query.argdefaults:
                    args_for_query[argname] = query.argdefaults[argname]
                else:
                    raise RuntimeError('Required argument "{}" for query "{}" not specified'.format(argname, query.name))

            return args_for_query

        def process_results_of_query(cursor):
            if query.rettype == QueryMetadata.RET_SINGLE_VALUE:
                row = cursor.fetchone()
                return None if row is None else row[0]

            elif query.rettype == QueryMetadata.RET_SINGLE_DICT:
                row = cursor.fetchone()
                if row is None:
                    return None
                names = [desc.name for desc in cursor.description]

                return dict(zip(names, row))

            elif query.rettype == QueryMetadata.RET_SINGLE_TUPLE:
                return cursor.fetchone()

            elif query.rettype == QueryMetadata.RET_ARRAY_OF_VALUES:
                return [row[0] for row in cursor.fetchall()]

            elif query.rettype == QueryMetadata.RET_ARRAY_OF_DICTS:
                names = [desc.name for desc in cursor.description]
                return [dict(zip(names, row)) for row in cursor.fetchall()]

            elif query.rettype == QueryMetadata.RET_ARRAY_OF_TUPLES:
                return cursor.fetchall()

            elif query.rettype == QueryMetadata.RET_ARRAY_OF_PACKAGES:
                names = [desc.name for desc in cursor.description]
                return [Package(**dict(zip(names, row))) for row in cursor.fetchall()]

            elif query.rettype == QueryMetadata.RET_DICT_AS_DICTS:
                names = [desc.name for desc in cursor.description]
                return {row[0]: dict(zip(names[1:], row[1:])) for row in cursor.fetchall()}

        def do_query(db, *args, **kwargs):
            with db.cursor() as cursor:
                arguments = prepare_arguments_for_query(args, kwargs)

                if isinstance(arguments, dict):
                    render = query.template.render(**arguments)
                else:
                    render = query.template.render()

                if query.argsmode == QueryMetadata.ARGSMODE_NORMAL:
                    cursor.execute(render, arguments)
                else:
                    cursor.executemany(render, arguments)

                return process_results_of_query(cursor)

        def do_explain_query(db, *args, **kwargs):
            with db.cursor() as cursor:
                arguments = prepare_arguments_for_query(args, kwargs)

                if isinstance(arguments, dict):
                    render = query.template.render(**arguments)
                else:
                    render = query.template.render()

                cursor.execute('EXPLAIN ANALYZE ' + render, arguments)

                return '\n'.join(map(lambda row: row[0], cursor.fetchall()))

        self._queries[query.name] = do_query
        self._queries['explain_' + query.name] = do_explain_query

    def inject_queries(self, target: Any, db: Any) -> None:
        for name, function in self._queries.items():
            setattr(target, name, functools.partial(function, db))
