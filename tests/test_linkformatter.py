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

# mypy: no-disallow-untyped-calls

import unittest

from repology.linkformatter import format_package_links

from .package import spawn_package


class TestLinkFormatter(unittest.TestCase):
    def test_basic(self) -> None:
        self.assertEqual(
            list(
                format_package_links(
                    spawn_package(
                        name='foo',
                        version='1.1',
                    ),
                    'https://example.com/{name}/{version}'
                )
            ),
            [
                'https://example.com/foo/1.1'
            ]
        )

    def test_filter(self) -> None:
        self.assertEqual(
            list(
                format_package_links(
                    spawn_package(
                        name='FOO',
                        version='1.1',
                    ),
                    'https://example.com/{name|lowercase}'
                )
            ),
            [
                'https://example.com/foo'
            ]
        )

    def test_list(self) -> None:
        package = spawn_package()
        package.extrafields = {'patch': ['foo', 'bar', 'baz'], 'suffix': ['a', 'b']}

        self.assertEqual(
            list(
                format_package_links(package, 'https://example.com/{patch}{suffix}')
            ),
            [
                'https://example.com/fooa',
                'https://example.com/foob',
                'https://example.com/bara',
                'https://example.com/barb',
                'https://example.com/baza',
                'https://example.com/bazb',
            ]
        )

    def test_raises(self) -> None:
        package = spawn_package()

        with self.assertRaises(RuntimeError):
            list(format_package_links(package, 'https://example.com/{unknown}'))

        self.assertEqual(list(format_package_links(package, 'https://example.com/{?unknown}')), [])

        with self.assertRaises(RuntimeError):
            list(format_package_links(package, 'https://example.com/{name|unknownfilter}'))


if __name__ == '__main__':
    unittest.main()
