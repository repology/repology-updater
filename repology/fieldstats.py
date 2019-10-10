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

from typing import Any, Iterable, List, Set


class FieldStatistics:
    _interesting_fields: Set[str]
    _used_fields: Set[str]

    def __init__(self, interesting_fields: Iterable[str]) -> None:
        self._interesting_fields = set(interesting_fields)
        self._used_fields = set()

    def add(self, item: Any) -> None:
        new_fields = False

        for field in self._interesting_fields:
            if getattr(item, field, None):
                self._used_fields.add(field)
                new_fields = True

        if new_fields:
            self._interesting_fields -= self._used_fields

    def get_used_fields(self) -> List[str]:
        return list(self._used_fields)
