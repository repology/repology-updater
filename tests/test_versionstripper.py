#!/usr/bin/env python3
#
# Copyright (C) 2018 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from repology.parsers.versions import VersionStripper


class TestVersionStripper(unittest.TestCase):
    def test_identity(self) -> None:
        self.assertEqual(VersionStripper()('1.2.3'), '1.2.3')

    def test_basic(self) -> None:
        self.assertEqual(VersionStripper().strip_left('.')('1.2.3'), '2.3')
        self.assertEqual(VersionStripper().strip_left_greedy('.')('1.2.3'), '3')
        self.assertEqual(VersionStripper().strip_right('.')('1.2.3'), '1.2')
        self.assertEqual(VersionStripper().strip_right_greedy('.')('1.2.3'), '1')

    def test_order(self) -> None:
        self.assertEqual(VersionStripper().strip_right('_').strip_right(',')('1_2,3_4'), '1_2')
        self.assertEqual(VersionStripper().strip_right(',').strip_right('_')('1_2,3_4'), '1')


if __name__ == '__main__':
    unittest.main()
