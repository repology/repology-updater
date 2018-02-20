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


from repology.package import Package


__all__ = ['QueryManager']


class QueryMetadataParsingError(RuntimeError):
    pass


class QueryLoadingError(RuntimeError):
    pass


class QueryMetadata:
    RET_NONE = 1
    RET_SINGLE_VALUE = 2
    RET_SINGLE_DICT = 3
    RET_SINGLE_TUPLE = 4
    RET_ARRAY_OF_VALUES = 5
    RET_ARRAY_OF_DICTS = 6
    RET_ARRAY_OF_PACKAGES = 7
    RET_DICT_AS_DICTS = 8

    def __init__(self):
        self.name = None
        self.query = ''
        self.args = []
        self.argdefaults = {}
        self.rettype = QueryMetadata.RET_NONE

    @staticmethod
    def parse_from_string(string):
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

        metadata = QueryMetadata()
        metadata.name = match.group(1).strip()

        for arg in match.group(2).split(','):
            arg = arg.strip()

            if not arg:
                continue

            argname, *argdefault = [s.strip() for s in arg.split('=', 1)]

            argdefault = argdefault[0] if argdefault else None

            if not argname:
                raise QueryMetadataParsingError('Cannot parse query metadata "{}": bad arguments'.format(string, argname))

            metadata.args.append(argname)

            if argdefault is None:
                pass
            elif argdefault.isdecimal():
                metadata.argdefaults[argname] = int(argdefault)
            elif argdefault.startswith('\''):
                metadata.argdefaults[argname] = argdefault.strip('\'')
            elif argdefault.startswith('\"'):
                metadata.argdefaults[argname] = argdefault.strip('\"')
            elif argdefault == 'True':
                metadata.argdefaults[argname] = True
            elif argdefault == 'False':
                metadata.argdefaults[argname] = False
            elif argdefault == 'None':
                metadata.argdefaults[argname] = None
            else:
                raise QueryMetadataParsingError('Cannot parse query metadata "{}": bad default value for argument "{}"'.format(string, argname))

        if not match.group(3):
            metadata.rettype = QueryMetadata.RET_NONE
        elif match.group(3) == 'single value':
            metadata.rettype = QueryMetadata.RET_SINGLE_VALUE
        elif match.group(3) == 'single dict':
            metadata.rettype = QueryMetadata.RET_SINGLE_DICT
        elif match.group(3) == 'single tuple':
            metadata.rettype = QueryMetadata.RET_SINGLE_TUPLE
        elif match.group(3) == 'array of values':
            metadata.rettype = QueryMetadata.RET_ARRAY_OF_VALUES
        elif match.group(3) == 'array of dicts':
            metadata.rettype = QueryMetadata.RET_ARRAY_OF_DICTS
        elif match.group(3) == 'array of packages':
            metadata.rettype = QueryMetadata.RET_ARRAY_OF_PACKAGES
        elif match.group(3) == 'dict of dicts':
            metadata.rettype = QueryMetadata.RET_DICT_AS_DICTS
        else:
            raise QueryMetadataParsingError('Cannot parse query metadata "{}": bad return specification'.format(string))

        return metadata


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

                    current_query = QueryMetadata.parse_from_string(match.group(1))

                if current_query is not None:
                    current_query.query += line

            if current_query is not None:
                self.__register_query(current_query)

    def __register_query(self, query):
        def do_query(db, *args, **kwargs):
            args_for_query = {}

            # prepare arguments
            for narg, argname in enumerate(query.args):
                if narg < len(args):
                    args_for_query[argname] = args[narg]
                elif argname in kwargs:
                    args_for_query[argname] = kwargs[argname]
                elif argname in query.argdefaults:
                    args_for_query[argname] = query.argdefaults[argname]
                else:
                    raise RuntimeError('Required argument "{}" for query "{}" not specified'.format(argname, query.name))

            with db.cursor() as cursor:
                # call
                cursor.execute(query.query, args_for_query)

                # handle return type
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

        self.queries[query.name] = do_query

    def InjectQueries(self, target, db):
        for name, function in self.queries.items():
            setattr(target, name, functools.partial(function, db))
