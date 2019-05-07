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
import math
from typing import List, Optional, Tuple


class GraphProcessor:
    _minval: Optional[float]
    _maxval: Optional[float]
    _points: List[Tuple[datetime.timedelta, float]]
    _float: bool

    def __init__(self) -> None:
        self._minval = None
        self._maxval = None
        self._points = []
        self._float = False

    def add_point(self, time: datetime.timedelta, value: float) -> None:
        # minor optimization of merging straight lines
        if len(self._points) >= 2 and value == self._points[-1][1] and value == self._points[-2][1]:
            del(self._points[-1])

        self._minval = value if self._minval is None else min(value, self._minval)
        self._maxval = value if self._maxval is None else max(value, self._maxval)
        self._points.append((time, value))
        if isinstance(value, float):
            self._float = True

    def get_points(self, period: int) -> List[Tuple[float, float]]:
        if self._minval is None or self._maxval is None:
            return []

        if self._minval == self._maxval:
            return [
                (
                    self._points[0][0].total_seconds() / period,
                    0.5
                ),
                (
                    self._points[-1][0].total_seconds() / period,
                    0.5
                )
            ]

        return [
            (
                point[0].total_seconds() / period,
                (point[1] - self._minval) / (self._maxval - self._minval)
            ) for point in self._points
        ]

    def get_y_ticks(self, suffix: str = '') -> List[Tuple[float, str]]:
        if self._minval is None or self._maxval is None:
            return []

        if self._minval == self._maxval:
            value = self._points[0][1]

            rounding = 0 if isinstance(value, int) else 3

            return [(0.5, '{:.{}f}{}'.format(value, rounding, suffix))]

        step = (self._maxval - self._minval) / 10

        steps: List[float] = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000]
        if self._float:
            steps = [0.001, 0.002, 0.005, 0.01, 0.02, 0.05, 0.1, 0.2, 0.5] + steps

        for roundedstep in steps:
            if roundedstep > step:
                step = roundedstep
                break

        rounding = 0
        if step < 0.01:
            rounding = 3
        elif step < 0.1:
            rounding = 2
        elif step < 1:
            rounding = 1

        lowtick = math.ceil(self._minval / step) * step
        numticks = int((self._maxval - lowtick) / step) + 1

        return [
            (
                (lowtick + step * n - self._minval) / (self._maxval - self._minval),
                '{:.{}f}{}'.format(lowtick + step * n, rounding, suffix)
            ) for n in range(numticks)
        ]
