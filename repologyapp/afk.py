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

import datetime
from typing import List, Optional, Tuple


class AFKChecker:
    _intervals: List[Tuple[datetime.date, datetime.date]]

    def __init__(self, intervals: List[str] = []) -> None:
        self._intervals = []

        for interval in intervals:
            start, *rest = [
                datetime.date(*map(int, date.split('-', 2)))
                for date in interval.split(' ', 1)
            ]

            self._intervals.append((start, rest[0] if rest else start))

    def get_afk_end(self, today: Optional[datetime.date] = None) -> Optional[datetime.date]:
        if today is None:
            today = datetime.date.today()

        for interval in self._intervals:
            if today >= interval[0] and today <= interval[1]:
                return interval[1]

        return None
