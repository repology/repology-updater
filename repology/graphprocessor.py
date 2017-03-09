#!/usr/bin/env python3
#
# Copyright (C) 2016 Dmitry Marakasov <amdmi3@amdmi3.ru>
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


class GraphProcessor:
    def __init__(self):
        self.minval = None
        self.maxval = None
        self.points = []

    def AddPoint(self, time, value):
        self.minval = value if self.minval is None else min(value, self.minval)
        self.maxval = value if self.maxval is None else max(value, self.maxval)
        self.points.append([time, value])

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

    def GetYTicks(self):
        if self.minval is None:
            return []

        if self.minval == self.maxval:
            return [(0.5, self.points[0][1])]

        step = (self.maxval - self.minval) / 10

        for roundedstep in (1, 2, 5, 10, 20, 50, 100, 200, 500, 1000, 2000, 5000, 10000, 20000, 50000, 100000):
            if roundedstep > step:
                step = roundedstep
                break

        return [
            (
                (val - self.minval) / (self.maxval - self.minval),
                val
            ) for val in range(((self.minval + step - 1) // step) * step, self.maxval + 1, step)
        ]
