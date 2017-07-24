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

from repology.package import Package
from repology.packageformatter import PackageFormatter


class TestVersionComparison(unittest.TestCase):
    def test_simple(self):
        pkg = Package(name='foo', version='1.0', origversion='1.0_1', category='devel', subrepo='main', extrafields={'foo': 'bar'})
        fmt = PackageFormatter()

        self.assertEqual(fmt.format('Just A String', pkg), 'Just A String')
        self.assertEqual(fmt.format('{name} {version} {origversion} {category} {subrepo} {foo}', pkg), 'foo 1.0 1.0_1 devel main bar')

    def test_empty_origversion(self):
        pkg = Package(name='foo', version='1.0')
        fmt = PackageFormatter()

        self.assertEqual(fmt.format('{origversion}', pkg), '1.0')


if __name__ == '__main__':
    unittest.main()
