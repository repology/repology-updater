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

from repology.logger import AccumulatingLogger, NoopLogger
from repology.packagemaker import PackageFactory


class TestPackageMaker(unittest.TestCase):
    def test_all_fields(self):
        factory = PackageFactory(NoopLogger())

        maker = factory.begin()
        maker.set_name_and_version('foo-1.0')
        maker.set_origin('/foo')
        maker.set_summary('foo package')
        maker.add_maintainers(None, 'a@com', [None, ['b@com']], None, 'c@com')
        maker.add_maintainers('d@com')
        maker.add_categories(None, 'foo', 'bar')
        maker.add_categories('baz')
        maker.add_homepages('http://foo', 'http://bar')
        maker.add_licenses(['GPLv2', 'GPLv3'])
        maker.add_licenses('MIT')
        maker.add_downloads(None, [None, 'http://baz'], ['ftp://quux'])
        pkg = maker.unwrap()

        self.assertEqual(pkg.name, 'foo')
        self.assertEqual(pkg.version, '1.0')
        self.assertEqual(pkg.extrafields['origin'], '/foo')
        self.assertEqual(pkg.maintainers, ['a@com', 'b@com', 'c@com', 'd@com'])
        self.assertEqual(pkg.category, 'foo')  # XXX: convert to array
        self.assertEqual(pkg.homepage, 'http://foo')  # XXX: convert to array
        self.assertEqual(pkg.licenses, ['GPLv2', 'GPLv3', 'MIT'])
        self.assertEqual(pkg.downloads, ['http://baz', 'ftp://quux'])

    def test_validate_urls(self):
        logger = AccumulatingLogger()
        factory = PackageFactory(logger)

        maker = factory.begin()
        maker.add_downloads('http://www.valid', 'https://www.valid/some', 'ftp://ftp.valid', 'invalid')
        pkg = maker.unwrap()

        self.assertEqual(pkg.downloads, ['http://www.valid', 'https://www.valid/some', 'ftp://ftp.valid'])
        self.assertEqual(len(logger.get()), 1)
        self.assertTrue('invalid' in logger.get()[0][0])

    def test_strip(self):
        factory = PackageFactory(NoopLogger())

        maker = factory.begin()
        maker.set_summary('       some package foo      ')
        pkg = maker.unwrap()

        self.assertEqual(pkg.comment, 'some package foo')

    def test_redefine(self):
        factory = PackageFactory(NoopLogger())

        maker = factory.begin()
        maker.set_name('foo')
        maker.set_name('bar')
        maker.set_version('1.0')
        maker.set_version('1.1')
        maker.set_summary('Foo')
        maker.set_summary('Bar')
        pkg = maker.unwrap()

        self.assertEqual(pkg.name, 'bar')
        self.assertEqual(pkg.version, '1.1')
        self.assertEqual(pkg.comment, 'Bar')

    def test_nulls(self):
        factory = PackageFactory(NoopLogger())

        maker = factory.begin()
        maker.set_name('foo')
        maker.set_name('')
        maker.set_name(None)
        maker.set_version('1.0')
        maker.set_version('')
        maker.set_version(None)
        maker.set_summary('Foo')
        maker.set_summary('')
        maker.set_summary(None)
        pkg = maker.unwrap()

        self.assertEqual(pkg.name, 'foo')
        self.assertEqual(pkg.version, '1.0')
        self.assertEqual(pkg.comment, 'Foo')


if __name__ == '__main__':
    unittest.main()
