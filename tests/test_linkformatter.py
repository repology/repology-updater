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

import pytest

from repology.linkformatter import format_package_links

from .package import spawn_package


def test_basic():
    assert list(
        format_package_links(
            spawn_package(
                name='foo',
                version='1.1',
            ),
            'https://example.com/{name}/{version}'
        )
    ) == [
        'https://example.com/foo/1.1'
    ]


def test_filter():
    assert list(
        format_package_links(
            spawn_package(
                name='FOO',
                version='1.1',
            ),
            'https://example.com/{name|lowercase}'
        )
    ) == [
        'https://example.com/foo'
    ]


def test_list():
    package = spawn_package()
    package.extrafields = {'patch': ['foo', 'bar', 'baz'], 'suffix': ['a', 'b']}

    assert list(
        format_package_links(package, 'https://example.com/{patch}{suffix}')
    ) == [
        'https://example.com/fooa',
        'https://example.com/foob',
        'https://example.com/bara',
        'https://example.com/barb',
        'https://example.com/baza',
        'https://example.com/bazb',
    ]


def test_raises():
    package = spawn_package()

    with pytest.raises(RuntimeError):
        list(format_package_links(package, 'https://example.com/{unknown}'))

    assert list(format_package_links(package, 'https://example.com/{?unknown}')) == []

    with pytest.raises(RuntimeError):
        list(format_package_links(package, 'https://example.com/{name|unknownfilter}'))
