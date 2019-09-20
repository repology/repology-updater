#!/usr/bin/env python3
#
# Copyright (C) 2018-2019 Dmitry Marakasov <amdmi3@amdmi3.ru>
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

from repologyapp.packageformatter import PackageFormatter

from .package import spawn_package


class TestPackageFormatter(unittest.TestCase):
    def test_simple(self) -> None:
        pkg = spawn_package(name='foo', keyname='foo/bar', version='1.0', origversion='1.0_1', category='devel', subrepo='main', extrafields={'foo': 'bar'})
        fmt = PackageFormatter()

        self.assertEqual(fmt.format('Just A String', pkg), 'Just A String')
        self.assertEqual(fmt.format('{name} {keyname} {version} {origversion} {category} {subrepo} {foo}', pkg), 'foo foo/bar 1.0 1.0_1 devel main bar')

    def test_filter_lowercase(self) -> None:
        fmt = PackageFormatter()

        self.assertEqual(fmt.format('{name|lowercase}', spawn_package(name='FOO', version='1.0')), 'foo')

    def test_filter_firstletter(self) -> None:
        fmt = PackageFormatter()

        self.assertEqual(fmt.format('{name|firstletter}', spawn_package(name='FOO', version='1.0')), 'f')
        self.assertEqual(fmt.format('{name|firstletter}', spawn_package(name='LIBFOO', version='1.0')), 'l')

    def test_filter_libfirstletter(self) -> None:
        fmt = PackageFormatter()

        self.assertEqual(fmt.format('{name|libfirstletter}', spawn_package(name='FOO', version='1.0')), 'f')
        self.assertEqual(fmt.format('{name|libfirstletter}', spawn_package(name='LIBFOO', version='1.0')), 'libf')

    def test_filter_stripdmo(self) -> None:
        fmt = PackageFormatter()

        self.assertEqual(fmt.format('{name|stripdmo}', spawn_package(name='mplayer')), 'mplayer')
        self.assertEqual(fmt.format('{name|stripdmo}', spawn_package(name='mplayer-dmo')), 'mplayer')

    def test_filter_basename(self) -> None:
        fmt = PackageFormatter()

        self.assertEqual(fmt.format('{keyname|basename}', spawn_package(keyname='foo/bar')), 'bar')
        self.assertEqual(fmt.format('{keyname|dirname}', spawn_package(keyname='foo/bar')), 'foo')

    def test_basename(self) -> None:
        fmt = PackageFormatter()

        self.assertEqual(fmt.format('{basename}', spawn_package(name='foo', basename='bar')), 'bar')
        self.assertEqual(fmt.format('{basename}', spawn_package(name='foo')), 'foo')

    def test_escaping(self) -> None:
        self.assertEqual(
            PackageFormatter().format(
                'package name is {name}',
                spawn_package(name='foo && $(bar) `date` "<>" \'<>\'')
            ),
            'package name is foo && $(bar) `date` "<>" \'<>\''
        )
        self.assertEqual(
            PackageFormatter(escape_mode='url').format(
                'http://example.com/{name}',
                spawn_package(name='foo && $(bar) `date` "<>" \'<>\'')
            ),
            'http://example.com/foo%20%26%26%20%24%28bar%29%20%60date%60%20%22%3C%3E%22%20%27%3C%3E%27'
        )
        self.assertEqual(
            PackageFormatter(escape_mode='shell').format(
                'echo {name}',
                spawn_package(name='foo && $(bar) `date` "<>" \'<>\'')
            ),
            """echo 'foo && $(bar) `date` "<>" '"'"'<>'"'"''"""
            # What we'd actually prefer is something more like:
            # 'echo foo\ \&\& \$\(bar\)\ \`date\`\ \"\<\>\"\ \'\<\>\''
        )


if __name__ == '__main__':
    unittest.main()
