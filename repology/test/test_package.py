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

from repology.package import Package, PackageFlags


class TestParsers(unittest.TestCase):
    def test_equality(self):
        self.assertEqual(Package(), Package())
        self.assertEqual(Package(name='a'), Package(name='a'))

        self.assertNotEqual(Package(name='a'), Package(name='b'))
        self.assertNotEqual(Package(), Package(name='b'))
        self.assertNotEqual(Package(name='a'), Package())

    def test_flag_p_is_patch(self):
        self.assertEqual(Package(version='1.0p1').VersionCompare(Package(version='1.0p1')), 0)
        self.assertEqual(Package(version='1.0p1', flags=PackageFlags.P_IS_PATCH).VersionCompare(Package(version='1.0p1')), 1)
        self.assertEqual(Package(version='1.0p1').VersionCompare(Package(version='1.0p1', flags=PackageFlags.P_IS_PATCH)), -1)
        self.assertEqual(Package(version='1.0p1', flags=PackageFlags.P_IS_PATCH).VersionCompare(Package(version='1.0p1', flags=PackageFlags.P_IS_PATCH)), 0)

    def test_flag_outdated(self):
        self.assertEqual(Package(version='1.0').VersionCompare(Package(version='1.0')), 0)
        self.assertEqual(Package(version='1.0', flags=PackageFlags.OUTDATED).VersionCompare(Package(version='1.0')), -1)
        self.assertEqual(Package(version='1.0').VersionCompare(Package(version='1.0', flags=PackageFlags.OUTDATED)), 1)
        self.assertEqual(Package(version='1.0', flags=PackageFlags.OUTDATED).VersionCompare(Package(version='1.0', flags=PackageFlags.OUTDATED)), 0)

    def test_flag_rolling(self):
        self.assertEqual(Package(version='1.0').VersionCompare(Package(version='1.0')), 0)
        self.assertEqual(Package(version='1.0', flags=PackageFlags.ROLLING).VersionCompare(Package(version='1.0')), 1)
        self.assertEqual(Package(version='1.0').VersionCompare(Package(version='1.0', flags=PackageFlags.ROLLING)), -1)
        self.assertEqual(Package(version='1.0', flags=PackageFlags.ROLLING).VersionCompare(Package(version='1.0', flags=PackageFlags.ROLLING)), 0)


if __name__ == '__main__':
    unittest.main()
