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

from repology.package import Package, PackageMergeConflict


class TestParsers(unittest.TestCase):
    def test_merge(self):
        pkg = Package()
        pkg.Merge(Package())
        self.assertEqual(pkg.name, None)

        pkg = Package()
        pkg.Merge(Package(name='foo'))
        self.assertEqual(pkg.name, 'foo')

        pkg = Package(name='foo')
        pkg.Merge(Package())
        self.assertEqual(pkg.name, 'foo')

        pkg = Package(name='foo')
        pkg.Merge(Package(name='foo'))
        self.assertEqual(pkg.name, 'foo')

        pkg = Package(name='foo')
        with self.assertRaises(PackageMergeConflict):
            pkg.Merge(Package(name='bar'))

    def test_normalize(self):
        pkg = Package(maintainers=['c', 'b', 'a'])
        pkg.Normalize()
        self.assertEqual(pkg.maintainers, ['a', 'b', 'c'])

        pkg = Package(homepage='http://example.com')
        pkg.Normalize()
        self.assertEqual(pkg.homepage, 'http://example.com/')

        pkg = Package(homepage='https://example.com')
        pkg.Normalize()
        self.assertEqual(pkg.homepage, 'https://example.com/')

        pkg = Package(homepage='http://example.com/')
        pkg.Normalize()
        self.assertEqual(pkg.homepage, 'http://example.com/')

        pkg = Package(homepage='https://example.com/')
        pkg.Normalize()
        self.assertEqual(pkg.homepage, 'https://example.com/')

        pkg = Package(homepage='http://example.com/foo')
        pkg.Normalize()
        self.assertEqual(pkg.homepage, 'http://example.com/foo')


if __name__ == '__main__':
    unittest.main()
