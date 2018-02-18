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

import os
import types


__all__ = ['QueryManager']


class QueryData:
    def __init__(self, name):
        self.name = name
        self.query = ''


class QueryManager:
    def __init__(self, queriesdir, db):
        self.db = db

        for filename in os.listdir(queriesdir):
            if filename.endswith('.sql'):
                self.__load_file(os.path.join(queriesdir, filename))

    def __load_file(self, path):
        current_query = None

        with open(path, 'r') as sqlfile:
            for line in sqlfile:
                if line.startswith('-- name:'):
                    if current_query is not None:
                        self.__register_query(current_query)
                    current_query = QueryData(line[8:].strip())

                else:
                    if current_query is not None:
                        current_query.query += line

            if current_query is not None:
                self.__register_query(current_query)

    def __register_query(self, query):
        def do_query(self):
            with self.db.cursor() as cursor:
                cursor.execute(query.query)

        setattr(self, query.name, types.MethodType(do_query, self))
