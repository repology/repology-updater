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
from typing import Any, Iterator, Optional

from repology.logger import AccumulatingLogger, Logger, NoopLogger
from repology.package import Package
from repology.packagemaker import NameType, PackageFactory, PackageMaker


class TestPackage:
    _factory: PackageFactory
    _package_maker: Optional[PackageMaker]
    _package: Optional[Package]

    def __init__(self, logger: Logger = NoopLogger()) -> None:
        self._factory = PackageFactory(logger)
        self._package_maker = None
        self._package = None

    def __enter__(self) -> PackageMaker:
        self._package_maker = self._factory.begin()
        self._package_maker.add_name('dummy_package', NameType.GENERIC_PKGNAME)
        self._package_maker.set_version('0dummy0')
        return self._package_maker

    def __exit__(self, *rest: Any) -> None:
        assert(self._package_maker)

        self._package = self._package_maker.spawn('dummy_repo', 'dummy_family')

    def __getattr__(self, key: str) -> Any:
        assert(self._package)
        return getattr(self._package, key)


class TestPackageMaker(unittest.TestCase):
    def test_all_fields(self) -> None:
        pkg = TestPackage()

        with pkg as maker:
            maker.add_name('foo', NameType.GENERIC_PKGNAME)
            maker.set_version('1.0')
            maker.set_summary('foo package')
            maker.add_maintainers(None, 'a@com', [None, ['b@com']], None, 'c@com')
            maker.add_maintainers('d@com')
            maker.add_categories(None, 'foo', 'bar')
            maker.add_categories('baz')
            maker.add_homepages('http://foo/', 'http://bar/')
            maker.add_licenses(['GPLv2', 'GPLv3'])
            maker.add_licenses('MIT')
            maker.add_downloads(None, [None, 'http://baz/'], ['ftp://quux/'])

        self.assertEqual(pkg.name, 'foo')
        self.assertEqual(pkg.version, '1.0')
        self.assertEqual(pkg.maintainers, ['a@com', 'b@com', 'c@com', 'd@com'])
        self.assertEqual(pkg.category, 'foo')  # XXX: convert to array
        self.assertEqual(pkg.homepage, 'http://foo/')  # XXX: convert to array
        self.assertEqual(pkg.licenses, ['GPLv2', 'GPLv3', 'MIT'])
        self.assertEqual(pkg.downloads, ['http://baz/', 'ftp://quux/'])

    def test_validate_urls(self) -> None:
        logger = AccumulatingLogger()
        pkg = TestPackage(logger)

        with pkg as maker:
            maker.add_downloads('http://www.valid/', 'https://www.valid/some', 'ftp://ftp.valid/', 'invalid')

        self.assertEqual(pkg.downloads, ['http://www.valid/', 'https://www.valid/some', 'ftp://ftp.valid/'])
        self.assertEqual(len(logger.get()), 1)
        self.assertTrue('invalid' in logger.get()[0])

    def test_normalize_urls(self) -> None:
        pkg = TestPackage()

        with pkg as maker:
            maker.add_homepages('Http://Foo.coM')
            maker.add_downloads('Http://Foo.coM')

        self.assertEqual(pkg.homepage, 'http://foo.com/')
        self.assertEqual(pkg.downloads, ['http://foo.com/'])

    def test_unicalization_with_order_preserved(self) -> None:
        pkg = TestPackage()

        with pkg as maker:
            maker.add_maintainers('z@com', 'y@com', 'x@com', 'z@com', 'y@com', 'x@com')
            maker.add_maintainers('z@com', 'y@com', 'x@com')

        self.assertEqual(pkg.maintainers, ['z@com', 'y@com', 'x@com'])

    def test_strip(self) -> None:
        pkg = TestPackage()

        with pkg as maker:
            maker.set_summary('       some package foo      ')

        self.assertEqual(pkg.comment, 'some package foo')

    def test_redefine(self) -> None:
        pkg = TestPackage()

        with pkg as maker:
            maker.add_name('foo', NameType.GENERIC_PKGNAME)
            maker.add_name('bar', NameType.GENERIC_PKGNAME)
            maker.set_version('1.0')
            maker.set_version('1.1')
            maker.set_summary('Foo')
            maker.set_summary('Bar')

        self.assertEqual(pkg.name, 'bar')
        self.assertEqual(pkg.version, '1.1')
        self.assertEqual(pkg.comment, 'Bar')

    def test_type_normalization1(self) -> None:
        pkg = TestPackage()

        with pkg as maker:
            maker.add_name(0, NameType.GENERIC_PKGNAME)
            maker.set_version(0)
            maker.set_summary(0)

        self.assertEqual(pkg.name, '0')
        self.assertEqual(pkg.version, '0')
        self.assertEqual(pkg.comment, '0')

    def test_type_normalization2(self) -> None:
        pkg = TestPackage()

        with pkg as maker:
            with self.assertRaises(RuntimeError):
                maker.add_name([123], NameType.GENERIC_PKGNAME)
            with self.assertRaises(RuntimeError):
                maker.set_version([123])
            with self.assertRaises(RuntimeError):
                maker.set_summary([123])

    def test_nulls(self) -> None:
        pkg = TestPackage()

        with pkg as maker:
            maker.add_name('foo', NameType.GENERIC_PKGNAME)
            maker.add_name('', NameType.GENERIC_PKGNAME)
            maker.add_name(None, NameType.GENERIC_PKGNAME)
            maker.set_version('1.0')
            maker.set_version('')
            maker.set_version(None)
            maker.set_summary('Foo')
            maker.set_summary('')
            maker.set_summary(None)

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

        pkg = TestPackage()

        with pkg as maker:
            maker.add_maintainers(iter_maintainers())

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


if __name__ == '__main__':
    unittest.main()
