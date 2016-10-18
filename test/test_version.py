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

from repology.util import VersionCompare

class TestVersionComparison(unittest.TestCase):
    def test_zeroes_at_right(self):
        self.assertEqual(VersionCompare("1", "1.0"), 0)
        self.assertEqual(VersionCompare("1", "1.0.0"), 0)

    def test_commutativity(self):
        self.assertEqual(VersionCompare("1.0", "1.1"), -1)
        self.assertEqual(VersionCompare("1.1", "1.0"), 1)

    def test_simple_comparisons(self):
        self.assertEqual(VersionCompare("0.0.0", "0.0.1"), -1)
        self.assertEqual(VersionCompare("0.0.1", "0.0.2"), -1)
        self.assertEqual(VersionCompare("0.0.2", "0.1.0"), -1)
        self.assertEqual(VersionCompare("0.0.2", "0.0.10"), -1)
        self.assertEqual(VersionCompare("0.0.10", "0.1.0"), -1)
        self.assertEqual(VersionCompare("0.1.0", "0.1.1"), -1)
        self.assertEqual(VersionCompare("0.1.1", "1.0.0"), -1)

    def test_bigger(self):
        self.assertEqual(VersionCompare("20160101", "20160102"), -1)

    def test_letter_component(self):
        self.assertEqual(VersionCompare("1.0", "1.0.a"), 1)
        self.assertEqual(VersionCompare("1.0.a", "1.0.b"), -1)

    def test_letter_addendum(self):
        self.assertEqual(VersionCompare("1.0", "1.0a"), -1)
        self.assertEqual(VersionCompare("1.0a", "1.0b"), -1)

    def test_miscomparation1(self):
        # #16
        self.assertEqual(VersionCompare("1.4c", "1.4e"), -1)

    def test_miscomparation2(self):
        # #16
        self.assertEqual(VersionCompare("4.89", "4.90.f"), -1)


if __name__ == '__main__':
    unittest.main()
