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

from repology.package import Package, PackageSanityCheckFailure, PackageSanityCheckProblem


class TestParsers(unittest.TestCase):
    def test_merge(self):
        pkg = Package()
        self.assertEqual(pkg.TryMerge(Package()), True)
        self.assertEqual(pkg.name, None)

        pkg = Package()
        self.assertEqual(pkg.TryMerge(Package(name='foo')), True)
        self.assertEqual(pkg.name, 'foo')

        pkg = Package(name='foo')
        self.assertEqual(pkg.TryMerge(Package()), True)
        self.assertEqual(pkg.name, 'foo')

        pkg = Package(name='foo')
        self.assertEqual(pkg.TryMerge(Package(name='foo')), True)
        self.assertEqual(pkg.name, 'foo')

        pkg = Package(name='foo')
        self.assertEqual(pkg.TryMerge(Package(name='bar')), False)

    def test_sanity_ok(self):
        Package(repo='r', family='f', name='n', effname='e', version='0').CheckSanity()

    def test_sanity_essential_fields_missing(self):
        with self.assertRaises(PackageSanityCheckFailure):
            Package(family='f', name='n', effname='e', version='0').CheckSanity()
        with self.assertRaises(PackageSanityCheckFailure):
            Package(repo='r', name='n', effname='e', version='0').CheckSanity()
        with self.assertRaises(PackageSanityCheckFailure):
            Package(repo='r', family='f', effname='e', version='0').CheckSanity()
        with self.assertRaises(PackageSanityCheckFailure):
            Package(repo='r', family='f', name='n', version='0').CheckSanity()
        with self.assertRaises(PackageSanityCheckFailure):
            Package(repo='r', family='f', name='n', effname='e').CheckSanity()

    def test_sanity_essential_fields_bad_type(self):
        with self.assertRaises(PackageSanityCheckFailure):
            Package(repo=['r'], family='f', name='n', effname='e', version='0').CheckSanity()
        with self.assertRaises(PackageSanityCheckFailure):
            Package(repo='r', family=['f'], name='n', effname='e', version='0').CheckSanity()
        with self.assertRaises(PackageSanityCheckFailure):
            Package(repo='r', family='f', name=['n'], effname='e', version='0').CheckSanity()
        with self.assertRaises(PackageSanityCheckFailure):
            Package(repo='r', family='f', name='n', effname=['e'], version='0').CheckSanity()
        with self.assertRaises(PackageSanityCheckFailure):
            Package(repo='r', family='f', name='n', effname='e', version=['0']).CheckSanity()

    def test_sanity_extra_fields_bad_type(self):
        with self.assertRaises(PackageSanityCheckFailure):
            Package(repo='r', family='f', name='n', effname='e', version='0', maintainers='foo').CheckSanity()
        with self.assertRaises(PackageSanityCheckFailure):
            Package(repo='r', family='f', name='n', effname='e', version='0', category=['foo']).CheckSanity()
        with self.assertRaises(PackageSanityCheckFailure):
            Package(repo='r', family='f', name='n', effname='e', version='0', comment=['foo']).CheckSanity()
        with self.assertRaises(PackageSanityCheckFailure):
            Package(repo='r', family='f', name='n', effname='e', version='0', homepage=['foo']).CheckSanity()
        with self.assertRaises(PackageSanityCheckFailure):
            Package(repo='r', family='f', name='n', effname='e', version='0', licenses='foo').CheckSanity()
        with self.assertRaises(PackageSanityCheckFailure):
            Package(repo='r', family='f', name='n', effname='e', version='0', downloads='foo').CheckSanity()
        with self.assertRaises(PackageSanityCheckFailure):
            Package(repo='r', family='f', name='n', effname='e', version='0', ignore=1).CheckSanity()
        with self.assertRaises(PackageSanityCheckFailure):
            Package(repo='r', family='f', name='n', effname='e', version='0', shadow=1).CheckSanity()
        with self.assertRaises(PackageSanityCheckFailure):
            Package(repo='r', family='f', name='n', effname='e', version='0', ignoreversion=1).CheckSanity()

    def test_sanity_essential_fields_bad_format(self):
        with self.assertRaises(PackageSanityCheckProblem):
            Package(repo='', family='f', name='n', effname='e', version='0').CheckSanity()
        with self.assertRaises(PackageSanityCheckProblem):
            Package(repo='r r', family='f', name='n', effname='e', version='0').CheckSanity()
        with self.assertRaises(PackageSanityCheckProblem):
            Package(repo='r', family='', name='n', effname='e', version='0').CheckSanity()
        with self.assertRaises(PackageSanityCheckProblem):
            Package(repo='r', family='f f', name='n', effname='e', version='0').CheckSanity()
        with self.assertRaises(PackageSanityCheckProblem):
            Package(repo='r', family='f', name='', effname='e', version='0').CheckSanity()
        with self.assertRaises(PackageSanityCheckProblem):
            Package(repo='r', family='f', name='n', effname='', version='0').CheckSanity()
        with self.assertRaises(PackageSanityCheckProblem):
            Package(repo='r', family='f', name='n', effname='e/e', version='0').CheckSanity()

    def test_sanity_extra_fields_bad_format(self):
        with self.assertRaises(PackageSanityCheckProblem):
            Package(repo='r', family='f', name='n', effname='e', version='0', maintainers=['']).CheckSanity()
        with self.assertRaises(PackageSanityCheckProblem):
            Package(repo='r', family='f', name='n', effname='e', version='0', maintainers=['a/a']).CheckSanity()
        with self.assertRaises(PackageSanityCheckProblem):
            Package(repo='r', family='f', name='n', effname='e', version='0', maintainers=[' a ']).CheckSanity()
        with self.assertRaises(PackageSanityCheckProblem):
            Package(repo='r', family='f', name='n', effname='e', version='0', maintainers=['a a']).CheckSanity()
        with self.assertRaises(PackageSanityCheckProblem):
            Package(repo='r', family='f', name='n', effname='e', version='0', maintainers=['a\na']).CheckSanity()

        with self.assertRaises(PackageSanityCheckProblem):
            Package(repo='r', family='f', name='n', effname='e', version='0', category='').CheckSanity()
        with self.assertRaises(PackageSanityCheckProblem):
            Package(repo='r', family='f', name='n', effname='e', version='0', category=' a ').CheckSanity()
        with self.assertRaises(PackageSanityCheckProblem):
            Package(repo='r', family='f', name='n', effname='e', version='0', category='a\na').CheckSanity()

        with self.assertRaises(PackageSanityCheckProblem):
            Package(repo='r', family='f', name='n', effname='e', version='0', comment='').CheckSanity()
        with self.assertRaises(PackageSanityCheckProblem):
            Package(repo='r', family='f', name='n', effname='e', version='0', comment=' a ').CheckSanity()
        with self.assertRaises(PackageSanityCheckProblem):
            Package(repo='r', family='f', name='n', effname='e', version='0', comment='a\na').CheckSanity()

        with self.assertRaises(PackageSanityCheckProblem):
            Package(repo='r', family='f', name='n', effname='e', version='0', homepage='').CheckSanity()
        with self.assertRaises(PackageSanityCheckProblem):
            Package(repo='r', family='f', name='n', effname='e', version='0', homepage=' a ').CheckSanity()
        with self.assertRaises(PackageSanityCheckProblem):
            Package(repo='r', family='f', name='n', effname='e', version='0', homepage='a a').CheckSanity()
        with self.assertRaises(PackageSanityCheckProblem):
            Package(repo='r', family='f', name='n', effname='e', version='0', homepage='a\na').CheckSanity()

        with self.assertRaises(PackageSanityCheckProblem):
            Package(repo='r', family='f', name='n', effname='e', version='0', downloads=['']).CheckSanity()
        with self.assertRaises(PackageSanityCheckProblem):
            Package(repo='r', family='f', name='n', effname='e', version='0', downloads=[' a ']).CheckSanity()
        with self.assertRaises(PackageSanityCheckProblem):
            Package(repo='r', family='f', name='n', effname='e', version='0', downloads=['a a']).CheckSanity()
        with self.assertRaises(PackageSanityCheckProblem):
            Package(repo='r', family='f', name='n', effname='e', version='0', downloads=['a\na']).CheckSanity()

        with self.assertRaises(PackageSanityCheckProblem):
            Package(repo='r', family='f', name='n', effname='e', version='0', licenses=['']).CheckSanity()
        with self.assertRaises(PackageSanityCheckProblem):
            Package(repo='r', family='f', name='n', effname='e', version='0', licenses=[' a ']).CheckSanity()
        with self.assertRaises(PackageSanityCheckProblem):
            Package(repo='r', family='f', name='n', effname='e', version='0', licenses=['a\na']).CheckSanity()

    def test_normalize_sort_maintainers(self):
        pkg = Package(maintainers=['c', 'b', 'a'])
        pkg.Normalize()
        self.assertEqual(pkg.maintainers, ['a', 'b', 'c'])

    def test_normalize_slash(self):
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

    def test_normalize_host_case(self):
        pkg = Package(homepage='HttP://ExamplE.CoM/FoO')
        pkg.Normalize()
        self.assertEqual(pkg.homepage, 'http://example.com/FoO')


if __name__ == '__main__':
    unittest.main()
