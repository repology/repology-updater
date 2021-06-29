#!/usr/bin/env python3
#
# Copyright (C) 2021 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from repology.package import PackageFlags
from repology.parsers.versions import parse_rpm_version


class TestRpmVersions(unittest.TestCase):
    def test_plain(self) -> None:
        self.assertEqual(parse_rpm_version([], '1.2', '1'), ('1.2', 0))
        self.assertEqual(parse_rpm_version(['foo'], '1.2', '1foo'), ('1.2', 0))
        self.assertEqual(parse_rpm_version(['foo'], '1.2', 'foo1'), ('1.2', 0))

    def test_snapshot_by_rpm_rev(self) -> None:
        self.assertEqual(parse_rpm_version([], '1.2', '0'), ('1.2', PackageFlags.IGNORE))
        self.assertEqual(parse_rpm_version(['foo'], '1.2', '0foo'), ('1.2', PackageFlags.IGNORE))
        self.assertEqual(parse_rpm_version(['foo'], '1.2', 'foo0'), ('1.2', PackageFlags.IGNORE))

    def test_known_prerelease(self) -> None:
        self.assertEqual(parse_rpm_version([], '1.2', '1.alpha1'), ('1.2-alpha1', 0))
        self.assertEqual(parse_rpm_version([], '1.2', '1.beta1'), ('1.2-beta1', 0))
        self.assertEqual(parse_rpm_version([], '1.2', '1.rc1'), ('1.2-rc1', 0))

    def test_snapshot(self) -> None:
        self.assertEqual(parse_rpm_version([], '1.2', '1.20210102'), ('1.2', PackageFlags.IGNORE))
        self.assertEqual(parse_rpm_version([], '1.2', '1.git1a2b3c4'), ('1.2', PackageFlags.IGNORE))


if __name__ == '__main__':
    unittest.main()
