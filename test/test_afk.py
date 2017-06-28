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

import unittest

from datetime import date

from repology.template_helpers import AFKChecker


class TestAFK(unittest.TestCase):
    def test_empty(self):
        afk = AFKChecker()

        self.assertEqual(afk.GetAFKEnd(), None)
        self.assertEqual(afk.GetAFKEnd(date(2017, 1, 1)), None)

    def test_day(self):
        afk = AFKChecker(['2017-01-02'])

        self.assertEqual(afk.GetAFKEnd(date(2017, 1, 1)), None)
        self.assertEqual(afk.GetAFKEnd(date(2017, 1, 2)), date(2017, 1, 2))
        self.assertEqual(afk.GetAFKEnd(date(2017, 1, 3)), None)

    def test_range(self):
        afk = AFKChecker(['2017-01-02 2017-01-04'])

        self.assertEqual(afk.GetAFKEnd(date(2017, 1, 1)), None)
        self.assertEqual(afk.GetAFKEnd(date(2017, 1, 2)), date(2017, 1, 4))
        self.assertEqual(afk.GetAFKEnd(date(2017, 1, 3)), date(2017, 1, 4))
        self.assertEqual(afk.GetAFKEnd(date(2017, 1, 4)), date(2017, 1, 4))
        self.assertEqual(afk.GetAFKEnd(date(2017, 1, 5)), None)

    def test_multi(self):
        afk = AFKChecker(['2017-01-02', '2017-01-04 2017-01-05'])

        self.assertEqual(afk.GetAFKEnd(date(2017, 1, 1)), None)
        self.assertEqual(afk.GetAFKEnd(date(2017, 1, 2)), date(2017, 1, 2))
        self.assertEqual(afk.GetAFKEnd(date(2017, 1, 3)), None)
        self.assertEqual(afk.GetAFKEnd(date(2017, 1, 4)), date(2017, 1, 5))
        self.assertEqual(afk.GetAFKEnd(date(2017, 1, 5)), date(2017, 1, 5))
        self.assertEqual(afk.GetAFKEnd(date(2017, 1, 6)), None)


if __name__ == '__main__':
    unittest.main()
