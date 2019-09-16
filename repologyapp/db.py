# Copyright (C) 2016-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from typing import Any, Optional, TYPE_CHECKING

import flask

import psycopg2

from repologyapp.config import config

from repology.querymgr import QueryManager


__all__ = [
    'get_db',
]


_querymgr = QueryManager(config['SQL_DIR'])


class Database:
    _db: Any  # no typing support for psycopg

    def __init__(self, dsn: str, querymgr: QueryManager, readonly: bool = True, autocommit: bool = False, application_name: Optional[str] = None) -> None:
        self._db = psycopg2.connect(dsn, application_name=application_name)
        self._db.set_session(readonly=readonly, autocommit=autocommit)
        querymgr.inject_queries(self, self._db)

    def commit(self) -> None:
        self._db.commit()

    # this class is filled by methods by querymgr
    # mypy doesn't know about them so we have to silence it this way
    if TYPE_CHECKING:
        def __getattr__(self, name: str) -> Any:
            pass


def get_db() -> Database:
    # XXX: this is not really a persistent DB connection!
    if not hasattr(flask.g, 'database'):
        flask.g.database = Database(config['DSN'], _querymgr, readonly=False, autocommit=True, application_name='repology-app')
    return flask.g.database  # type: ignore
