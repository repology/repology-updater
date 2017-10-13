# Copyright (C) 2016-2017 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

import math


class GraphProcessor:
    def __init__(self):
        self.minval = None
        self.maxval = None
        self.points = []
        self.float = False

    def AddPoint(self, time, value):
        # minor optimization of merging straight lines
        if len(self.points) >= 2 and value == self.points[-1][1] and value == self.points[-2][1]:
            del(self.points[-1])

        self.minval = value if self.minval is None else min(value, self.minval)
        self.maxval = value if self.maxval is None else max(value, self.maxval)
        self.points.append([time, value])
        if isinstance(value, float):
            self.float = True

    def GetPoints(self, period):
        if self.minval is None:
            return []

        if self.minval == self.maxval:
            return [
                (
                    self.points[0][0].total_seconds() / period,
                    0.5
                ),
                (
                    self.points[-1][0].total_seconds() / period,
                    0.5
                )
            ]

        return [
            (
                point[0].total_seconds() / period,
                (point[1] - self.minval) / (self.maxval - self.minval)
            ) for point in self.points
        ]

    def GetYTicks(self, suffix=''):
        if self.minval is None:
            return []

        if self.minval == self.maxval:
            value = self.points[0][1]

            rounding = 0 if isinstance(value, int) else 3

            return [(0.5, '{:.{}f}{}'.format(value, rounding, suffix))]

        step = (self.maxval - self.minval) / 10

        steps = [1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000]
        if self.float:
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

        lowtick = math.ceil(self.minval / step) * step
        numticks = int((self.maxval - lowtick) / step) + 1

        return [
            (
                (lowtick + step * n - self.minval) / (self.maxval - self.minval),
                '{:.{}f}{}'.format(lowtick + step * n, rounding, suffix)
            ) for n in range(numticks)
        ]
