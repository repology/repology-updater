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

import functools
import os
import re

import jinja2

from repology.package import Package


__all__ = ['QueryManager']


class QueryMetadataParsingError(RuntimeError):
    pass


class QueryLoadingError(RuntimeError):
    pass


class QueryMetadata:
    RET_NONE = 0
    RET_SINGLE_VALUE = 1
    RET_SINGLE_DICT = 2
    RET_SINGLE_TUPLE = 3
    RET_ARRAY_OF_VALUES = 4
    RET_ARRAY_OF_DICTS = 5
    RET_ARRAY_OF_PACKAGES = 6
    RET_DICT_AS_DICTS = 7

    ARGSMODE_NORMAL = 0
    ARGSMODE_MANY_VALUES = 1

    def __init__(self):
        self.name = None
        self.query = ''
        self.template = None
        self.args = []
        self.argdefaults = {}
        self.rettype = QueryMetadata.RET_NONE
        self.argsmode = QueryMetadata.ARGSMODE_NORMAL

    def parse(self, string):
        """Parse query metadata from the string definition.

        Input examples:

            - funcname()
            Takes no arguments, returns nothing

            - funcname(arg)
            Takes single argument, returns nothing

            - funcname(arg1, arg2=True, arg3=False, arg4=123, arg5="str") -> scalar
            Takes 5 arguments, some with default values, returns single value
        """
        match = re.match('\s*([a-z][a-z0-9_]*)\s*\(([^)]*)\)(?:\s*->\s*([a-z ]+))?', string)
        if match is None:
            raise QueryMetadataParsingError('Cannot parse query metadata "{}"'.format(string))

        self.name = match.group(1).strip()
        self.parse_arguments(match.group(2))
        self.parse_return_type(match.group(3))

    def parse_arguments(self, string):
        if string:
            string = string.strip()

        if string == 'many values':
            self.argsmode = QueryMetadata.ARGSMODE_MANY_VALUES
            return

        for arg in string.split(','):
            arg = arg.strip()

            if not arg:
                continue

            argname, *argdefault = [s.strip() for s in arg.split('=', 1)]

            argdefault = argdefault[0] if argdefault else None

            if not argname:
                raise QueryMetadataParsingError('Cannot parse query metadata "{}": bad arguments'.format(string, argname))

            self.args.append(argname)

            if argdefault is None:
                pass
            elif argdefault.isdecimal():
                self.argdefaults[argname] = int(argdefault)
            elif argdefault.startswith('\''):
                self.argdefaults[argname] = argdefault.strip('\'')
            elif argdefault.startswith('\"'):
                self.argdefaults[argname] = argdefault.strip('\"')
            elif argdefault == 'True':
                self.argdefaults[argname] = True
            elif argdefault == 'False':
                self.argdefaults[argname] = False
            elif argdefault == 'None':
                self.argdefaults[argname] = None
            else:
                raise QueryMetadataParsingError('Cannot parse query metadata "{}": bad default value for argument "{}"'.format(string, argname))

    def parse_return_type(self, string):
        if string:
            string = string.strip()

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
        elif string == 'array of packages':
            self.rettype = QueryMetadata.RET_ARRAY_OF_PACKAGES
        elif string == 'dict of dicts':
            self.rettype = QueryMetadata.RET_DICT_AS_DICTS
        else:
            raise QueryMetadataParsingError('Cannot parse query metadata "{}": bad return specification'.format(string))


class QueryManager:
    def __init__(self, queriesdir):
        self.queries = {}

        for filename in os.listdir(queriesdir):
            if filename.endswith('.sql'):
                try:
                    self.__load_file(os.path.join(queriesdir, filename))
                except QueryMetadataParsingError as e:
                    raise QueryLoadingError('Cannot load SQL queries from {}: {}'.format(filename, str(e)))

    def __load_file(self, path):
        current_query = None

        with open(path, 'r', encoding='utf-8') as sqlfile:
            for line in sqlfile:
                match = re.match('--\s*!!(.*)', line)
                if match:
                    if current_query is not None:
                        self.__register_query(current_query)

                    current_query = QueryMetadata()
                    current_query.parse(match.group(1))

                if current_query is not None:
                    current_query.query += line

            if current_query is not None:
                self.__register_query(current_query)

    def __register_query(self, query):
        query.template = jinja2.Template(query.query)

        def prepare_arguments_for_query(args, kwargs):
            if query.argsmode == QueryMetadata.ARGSMODE_MANY_VALUES:
                return [[value] for value in args[0]]

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

        self.queries[query.name] = do_query

    def InjectQueries(self, target, db):
        for name, function in self.queries.items():
            setattr(target, name, functools.partial(function, db))
