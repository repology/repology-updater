# Copyright (C) 2018-2021 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from typing import Any, Iterator

import pytest

from repology.logger import AccumulatingLogger, NoopLogger
from repology.package import LinkType, Package
from repology.packagemaker import NameType, PackageFactory, PackageMaker


class PackageMakerWrapper:
    _logger: AccumulatingLogger
    _factory: PackageFactory
    _package_maker: PackageMaker | None
    _package: Package | None

    def __init__(self) -> None:
        self._logger = AccumulatingLogger()
        self._factory = PackageFactory(self._logger)
        self._package_maker = None
        self._package = None

    def __enter__(self) -> PackageMaker:
        self._package_maker = self._factory.begin()
        self._package_maker.add_name('dummy_package', NameType.GENERIC_GEN_NAME)
        self._package_maker.set_version('0dummy0')
        return self._package_maker

    def __exit__(self, *rest: Any) -> None:
        assert self._package_maker

        self._package = self._package_maker.spawn('dummy_repo', 'dummy_family')

    def __getattr__(self, key: str) -> Any:
        assert self._package
        return getattr(self._package, key)

    def get_logger(self) -> AccumulatingLogger:
        return self._logger


@pytest.fixture
def pkg() -> PackageMakerWrapper:
    return PackageMakerWrapper()


def test_all_fields(pkg):
    with pkg as maker:
        maker.add_name('foo', NameType.GENERIC_GEN_NAME)
        maker.set_version('1.0')
        maker.set_summary('foo package')
        maker.add_maintainers(None, 'a@com', [None, ['b@com']], None, 'c@com')
        maker.add_maintainers('d@com')
        maker.add_categories(None, 'foo', 'bar')
        maker.add_categories('baz')
        maker.add_homepages('http://foo/', ['http://bar/'])
        maker.add_licenses(['GPLv2', 'GPLv3'])
        maker.add_licenses('MIT')
        maker.add_downloads(None, [None, 'http://baz/'], 'ftp://quux/')
        maker.add_links(LinkType.OTHER, [['http://yyy/'], None], None, 'http://xxx/')

    assert pkg.name == 'foo'
    assert pkg.version == '1.0'
    assert pkg.maintainers == ['a@com', 'b@com', 'c@com', 'd@com']
    assert pkg.category == 'foo'  # XXX: convert to array
    assert pkg.licenses == ['GPLv2', 'GPLv3', 'MIT']
    assert pkg.links == \
        [
            (LinkType.UPSTREAM_HOMEPAGE, 'http://foo/'),
            (LinkType.UPSTREAM_HOMEPAGE, 'http://bar/'),
            (LinkType.UPSTREAM_DOWNLOAD, 'http://baz/'),
            (LinkType.UPSTREAM_DOWNLOAD, 'ftp://quux/'),
            (LinkType.OTHER, 'http://yyy/'),
            (LinkType.OTHER, 'http://xxx/'),
        ]


def test_validate_urls(pkg):
    with pkg as maker:
        maker.add_downloads('http://www.valid/', 'https://www.valid/some', 'ftp://ftp.valid/', 'invalid')

    assert pkg.links == \
        [
            (LinkType.UPSTREAM_DOWNLOAD, 'http://www.valid/'),
            (LinkType.UPSTREAM_DOWNLOAD, 'https://www.valid/some'),
            (LinkType.UPSTREAM_DOWNLOAD, 'ftp://ftp.valid/'),
        ]
    assert len(pkg.get_logger().get()) == 1
    assert 'invalid' in pkg.get_logger().get()[0]


def test_normalize_urls(pkg):
    with pkg as maker:
        maker.add_homepages('Http://Foo.coM')
        maker.add_downloads('Http://Foo.coM')

    assert pkg.links == \
        [
            (LinkType.UPSTREAM_HOMEPAGE, 'http://foo.com/'),
            (LinkType.UPSTREAM_DOWNLOAD, 'http://foo.com/'),
        ]


def test_unicalization_with_order_preserved(pkg):
    with pkg as maker:
        maker.add_maintainers('z@com', 'y@com', 'x@com', 'z@com', 'y@com', 'x@com')
        maker.add_maintainers('z@com', 'y@com', 'x@com')

    assert pkg.maintainers == ['z@com', 'y@com', 'x@com']


def test_strip(pkg):
    with pkg as maker:
        maker.set_summary('       some package foo      ')

    assert pkg.comment == 'some package foo'


def test_redefine(pkg):
    with pkg as maker:
        maker.add_name('foo', NameType.GENERIC_GEN_NAME)
        maker.add_name('bar', NameType.GENERIC_GEN_NAME)
        maker.set_version('1.0')
        maker.set_version('1.1')
        maker.set_summary('Foo')
        maker.set_summary('Bar')

    assert pkg.name == 'bar'
    assert pkg.version == '1.1'
    assert pkg.comment == 'Bar'


def test_type_normalization1(pkg):
    with pkg as maker:
        maker.add_name(0, NameType.GENERIC_GEN_NAME)
        maker.set_version(0)
        maker.set_summary(0)

    assert pkg.name == '0'
    assert pkg.version == '0'
    assert pkg.comment == '0'


def test_type_normalization2(pkg):
    with pkg as maker:
        with pytest.raises(RuntimeError):
            maker.add_name([123], NameType.GENERIC_GEN_NAME)
        with pytest.raises(RuntimeError):
            maker.set_version([123])
        with pytest.raises(RuntimeError):
            maker.set_summary([123])


def test_nulls(pkg):
    with pkg as maker:
        maker.add_name('foo', NameType.GENERIC_GEN_NAME)
        maker.add_name('', NameType.GENERIC_GEN_NAME)
        maker.add_name(None, NameType.GENERIC_GEN_NAME)
        maker.set_version('1.0')
        maker.set_version('')
        maker.set_version(None)
        maker.set_summary('Foo')
        maker.set_summary('')
        maker.set_summary(None)

    assert pkg.name == 'foo'
    assert pkg.version == '1.0'
    assert pkg.comment == 'Foo'


def test_iter(pkg):
    def iter_maintainers() -> Iterator[Any]:
        yield 'a@com'
        yield ['b@com', None, '', 'c@com']
        yield None
        yield ''
        yield 'd@com'

    with pkg as maker:
        maker.add_maintainers(iter_maintainers())

    assert pkg.maintainers == ['a@com', 'b@com', 'c@com', 'd@com']


def test_clone():
    factory = PackageFactory(NoopLogger())

    pkg1 = factory.begin('pkg1')
    pkg1.add_maintainers('foo')

    pkg2 = pkg1.clone('pkg2')
    pkg2.add_maintainers('bar')

    pkg3 = pkg1.clone(append_ident='pkg3')
    pkg3.add_maintainers('baz')

    assert pkg1.maintainers == ['foo']
    assert pkg2.maintainers == ['foo', 'bar']
    assert pkg3.maintainers == ['foo', 'baz']


def test_ident():
    logger = AccumulatingLogger()

    factory = PackageFactory(logger)

    pkg1 = factory.begin('pkg1')
    pkg1.log('')
    pkg2 = pkg1.clone('pkg2')
    pkg2.log('')
    pkg3 = pkg1.clone(append_ident='pkg3')
    pkg3.log('')

    assert 'pkg1:' in logger.get()[0]

    assert 'pkg2:' in logger.get()[1]
    assert 'pkg1:' not in logger.get()[1]

    assert 'pkg1pkg3:' in logger.get()[2]
    assert 'pkg2:' not in logger.get()[2]
