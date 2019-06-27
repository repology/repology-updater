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

# mypy: no-disallow-untyped-calls

import unittest
from typing import Any, Iterator

from repology.logger import AccumulatingLogger, NoopLogger
from repology.packagemaker import PackageFactory


class TestPackageMaker(unittest.TestCase):
    def test_all_fields(self) -> None:
        factory = PackageFactory(NoopLogger())

        maker = factory.begin()
        maker.set_name_and_version('foo-1.0')
        maker.set_origin('/foo')
        maker.set_summary('foo package')
        maker.add_maintainers(None, 'a@com', [None, ['b@com']], None, 'c@com')
        maker.add_maintainers('d@com')
        maker.add_categories(None, 'foo', 'bar')
        maker.add_categories('baz')
        maker.add_homepages('http://foo/', 'http://bar/')
        maker.add_licenses(['GPLv2', 'GPLv3'])
        maker.add_licenses('MIT')
        maker.add_downloads(None, [None, 'http://baz/'], ['ftp://quux/'])
        pkg = maker.unwrap()

        self.assertEqual(pkg.name, 'foo')
        self.assertEqual(pkg.version, '1.0')
        self.assertEqual(pkg.extrafields['origin'], '/foo')
        self.assertEqual(pkg.maintainers, ['a@com', 'b@com', 'c@com', 'd@com'])
        self.assertEqual(pkg.category, 'foo')  # XXX: convert to array
        self.assertEqual(pkg.homepage, 'http://foo/')  # XXX: convert to array
        self.assertEqual(pkg.licenses, ['GPLv2', 'GPLv3', 'MIT'])
        self.assertEqual(pkg.downloads, ['http://baz/', 'ftp://quux/'])

    def test_validate_urls(self) -> None:
        logger = AccumulatingLogger()
        factory = PackageFactory(logger)

        maker = factory.begin()
        maker.add_downloads('http://www.valid/', 'https://www.valid/some', 'ftp://ftp.valid/', 'invalid')
        pkg = maker.unwrap()

        self.assertEqual(pkg.downloads, ['http://www.valid/', 'https://www.valid/some', 'ftp://ftp.valid/'])
        self.assertEqual(len(logger.get()), 1)
        self.assertTrue('invalid' in logger.get()[0])

    def test_normalize_urls(self) -> None:
        factory = PackageFactory(NoopLogger())

        maker = factory.begin()
        maker.add_homepages('Http://Foo.coM')
        maker.add_downloads('Http://Foo.coM')
        pkg = maker.unwrap()

        self.assertEqual(pkg.homepage, 'http://foo.com/')
        self.assertEqual(pkg.downloads, ['http://foo.com/'])

    def test_unicalization_with_order_preserved(self) -> None:
        factory = PackageFactory(NoopLogger())

        maker = factory.begin()
        maker.add_maintainers('z@com', 'y@com', 'x@com', 'z@com', 'y@com', 'x@com')
        maker.add_maintainers('z@com', 'y@com', 'x@com')
        pkg = maker.unwrap()

        self.assertEqual(pkg.maintainers, ['z@com', 'y@com', 'x@com'])

    def test_strip(self) -> None:
        factory = PackageFactory(NoopLogger())

        maker = factory.begin()
        maker.set_summary('       some package foo      ')
        pkg = maker.unwrap()

        self.assertEqual(pkg.comment, 'some package foo')

    def test_redefine(self) -> None:
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

    def test_type_normalization1(self) -> None:
        factory = PackageFactory(NoopLogger())

        maker = factory.begin()
        maker.set_name(0)
        maker.set_version(0)
        maker.set_summary(0)
        pkg = maker.unwrap()

        self.assertEqual(pkg.name, '0')
        self.assertEqual(pkg.version, '0')
        self.assertEqual(pkg.comment, '0')

    def test_type_normalization2(self) -> None:
        factory = PackageFactory(NoopLogger())

        maker = factory.begin()

        with self.assertRaises(RuntimeError):
            maker.set_name([123])
        with self.assertRaises(RuntimeError):
            maker.set_version([123])
        with self.assertRaises(RuntimeError):
            maker.set_summary([123])

    def test_nulls(self) -> None:
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

    def test_iter(self) -> None:
        def iter_maintainers() -> Iterator[Any]:
            yield 'a@com'
            yield ['b@com', None, '', 'c@com']
            yield None
            yield ''
            yield 'd@com'

        factory = PackageFactory(NoopLogger())

        maker = factory.begin()
        maker.add_maintainers(iter_maintainers())
        pkg = maker.unwrap()

        self.assertEqual(pkg.maintainers, ['a@com', 'b@com', 'c@com', 'd@com'])

    def test_clone(self) -> None:
        factory = PackageFactory(NoopLogger())

        pkg1 = factory.begin('pkg1')
        pkg1.add_maintainers('foo')

        pkg2 = pkg1.clone('pkg2')
        pkg2.add_maintainers('bar')

        pkg3 = pkg1.clone(append_ident='pkg3')
        pkg3.add_maintainers('baz')

        self.assertEqual(pkg1.maintainers, ['foo'])
        self.assertEqual(pkg2.maintainers, ['foo', 'bar'])
        self.assertEqual(pkg3.maintainers, ['foo', 'baz'])

    def test_ident(self) -> None:
        logger = AccumulatingLogger()

        factory = PackageFactory(logger)

        pkg1 = factory.begin('pkg1')
        pkg1.log('')
        pkg2 = pkg1.clone('pkg2')
        pkg2.log('')
        pkg3 = pkg1.clone(append_ident='pkg3')
        pkg3.log('')

        self.assertTrue('pkg1:' in logger.get()[0])

        self.assertTrue('pkg2:' in logger.get()[1])
        self.assertTrue('pkg1:' not in logger.get()[1])

        self.assertTrue('pkg1pkg3:' in logger.get()[2])
        self.assertTrue('pkg2:' not in logger.get()[2])

    def test_sanity(self) -> None:
        factory = PackageFactory(NoopLogger())

        maker = factory.begin()

        self.assertFalse(maker.check_sanity())

        maker.set_name('foo')

        self.assertFalse(maker.check_sanity())

        maker.set_version('1.0')

        self.assertTrue(maker.check_sanity())


if __name__ == '__main__':
    unittest.main()
