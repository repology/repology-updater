# Copyright (C) 2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import sqlite3
from typing import Any, Iterable, Sequence


def iter_sqlite(path: str, table_expr: str, columns: Sequence[str]) -> Iterable[dict[str, Any]]:
    try:
        conn = sqlite3.connect('file:{}?mode=ro'.format(path))
        cur = conn.cursor()

        cur.execute('SELECT {} FROM {}'.format(','.join(columns), table_expr))

        while True:
            row = cur.fetchone()
            if row is None:
                break

            yield dict(zip(columns, row))
    finally:
        if conn:
            conn.close()
