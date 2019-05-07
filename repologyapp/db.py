# Copyright (C) 2016-2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import flask

from repologyapp.config import config

from repology.database import Database
from repology.querymgr import QueryManager


__all__ = [
    'get_db',
]


_querymgr = QueryManager(config['SQL_DIR'])


def get_db() -> Database:
    # XXX: this is not really a persistent DB connection!
    if not hasattr(flask.g, 'database'):
        flask.g.database = Database(config['DSN'], _querymgr, readonly=False, autocommit=True, application_name='repology-app')
    return flask.g.database  # type: ignore
