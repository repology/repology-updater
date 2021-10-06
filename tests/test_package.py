# Copyright (C) 2016-2021 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from repology.package import LinkType, Package, PackageFlags

from .package import spawn_package


def assert_version_compare(a: Package, b: Package, res: int) -> None:
    assert a.version_compare(b) == res


def test_equality() -> None:
    assert spawn_package() == spawn_package()
    assert spawn_package(name='a') == spawn_package(name='a')
    assert spawn_package(
        links=[
            (LinkType.UPSTREAM_HOMEPAGE, 'http://foo'),
            (LinkType.UPSTREAM_HOMEPAGE, 'http://foo'),
            (LinkType.UPSTREAM_HOMEPAGE, 'http://bar'),
            (LinkType.UPSTREAM_HOMEPAGE, 'http://bar'),
        ]
    ) == spawn_package(
        links=[
            (LinkType.UPSTREAM_HOMEPAGE, 'http://foo'),
            (LinkType.UPSTREAM_HOMEPAGE, 'http://bar'),
        ]
    )

    assert spawn_package(name='a') != spawn_package(name='b')
    assert spawn_package() != spawn_package(name='b')
    assert spawn_package(name='a') != spawn_package()


def test_flag_p_is_patch() -> None:
    assert_version_compare(
        spawn_package(version='1.0p1'), spawn_package(version='1.0p1'), 0
    )
    assert_version_compare(
        spawn_package(version='1.0p1', flags=PackageFlags.P_IS_PATCH),
        spawn_package(version='1.0p1'),
        1,
    )
    assert_version_compare(
        spawn_package(version='1.0p1'),
        spawn_package(version='1.0p1', flags=PackageFlags.P_IS_PATCH),
        -1,
    )
    assert_version_compare(
        spawn_package(version='1.0p1', flags=PackageFlags.P_IS_PATCH),
        spawn_package(version='1.0p1', flags=PackageFlags.P_IS_PATCH),
        0,
    )


def test_flag_sink() -> None:
    assert_version_compare(
        spawn_package(version='1.0'), spawn_package(version='1.0'), 0
    )
    assert_version_compare(
        spawn_package(version='1.0', flags=PackageFlags.SINK),
        spawn_package(version='1.0'),
        -1,
    )
    assert_version_compare(
        spawn_package(version='1.0'),
        spawn_package(version='1.0', flags=PackageFlags.SINK),
        1,
    )
    assert_version_compare(
        spawn_package(version='1.0', flags=PackageFlags.SINK),
        spawn_package(version='1.0', flags=PackageFlags.SINK),
        0,
    )


def test_flag_rolling() -> None:
    assert_version_compare(
        spawn_package(version='1.0'), spawn_package(version='1.0'), 0
    )
    assert_version_compare(
        spawn_package(version='1.0', flags=PackageFlags.ROLLING),
        spawn_package(version='1.0'),
        1,
    )
    assert_version_compare(
        spawn_package(version='1.0'),
        spawn_package(version='1.0', flags=PackageFlags.ROLLING),
        -1,
    )
    assert_version_compare(
        spawn_package(version='1.0', flags=PackageFlags.ROLLING),
        spawn_package(version='1.0', flags=PackageFlags.ROLLING),
        0,
    )


def test_hash() -> None:
    assert (
        spawn_package(
            name='foo',
            version='1.0',
            links=[
                (LinkType.UPSTREAM_HOMEPAGE, 'http://foo'),
                (LinkType.UPSTREAM_HOMEPAGE, 'http://bar'),
            ],
        ).get_classless_hash()
        == spawn_package(
            name='foo',
            version='1.0',
            links=[
                (LinkType.UPSTREAM_HOMEPAGE, 'http://foo'),
                (LinkType.UPSTREAM_HOMEPAGE, 'http://bar'),
            ],
        ).get_classless_hash()
    )

    assert (
        spawn_package(name='foo', version='1.0').get_classless_hash()
        != spawn_package(name='foo', version='1.1').get_classless_hash()
    )
    assert (
        spawn_package(name='foo', version='1.0').get_classless_hash()
        != spawn_package(name='foO', version='1.0').get_classless_hash()
    )
