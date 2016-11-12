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

from repology.parser.gentoo import IsBetterVersion

class TestGentooIsBetterVersion(unittest.TestCase):
    def test_againstnone(self):
        self.assertEqual(IsBetterVersion("0", None), True)
        self.assertEqual(IsBetterVersion("1", None), True)
        self.assertEqual(IsBetterVersion("9999", None), True)

    def test_againstver(self):
        self.assertEqual(IsBetterVersion("0", "1"), False)
        self.assertEqual(IsBetterVersion("1", "0"), True)

    def test_agains9999(self):
        self.assertEqual(IsBetterVersion("1", "9999"), True)
        self.assertEqual(IsBetterVersion("9999", "1"), False)


if __name__ == '__main__':
    unittest.main()
