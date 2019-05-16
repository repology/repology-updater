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

from repologyapp.packageformatter import PackageFormatter

from repology.package import Package


class TestVersionComparison(unittest.TestCase):
    def test_simple(self):
        pkg = Package(name='foo', version='1.0', origversion='1.0_1', category='devel', subrepo='main', extrafields={'foo': 'bar'})
        fmt = PackageFormatter()

        self.assertEqual(fmt.format('Just A String', pkg), 'Just A String')
        self.assertEqual(fmt.format('{name} {version} {origversion} {category} {subrepo} {foo}', pkg), 'foo 1.0 1.0_1 devel main bar')

    def test_filter_lowercase(self):
        fmt = PackageFormatter()

        self.assertEqual(fmt.format('{name|lowercase}', Package(name='FOO', version='1.0')), 'foo')

    def test_filter_firstletter(self):
        fmt = PackageFormatter()

        self.assertEqual(fmt.format('{name|firstletter}', Package(name='FOO', version='1.0')), 'f')
        self.assertEqual(fmt.format('{name|firstletter}', Package(name='LIBFOO', version='1.0')), 'l')

    def test_filter_libfirstletter(self):
        fmt = PackageFormatter()

        self.assertEqual(fmt.format('{name|libfirstletter}', Package(name='FOO', version='1.0')), 'f')
        self.assertEqual(fmt.format('{name|libfirstletter}', Package(name='LIBFOO', version='1.0')), 'libf')

    def test_basename(self):
        fmt = PackageFormatter()

        self.assertEqual(fmt.format('{basename}', Package(name='foo', basename='bar')), 'bar')
        self.assertEqual(fmt.format('{basename}', Package(name='foo')), 'foo')

    def test_escaping(self):
        self.assertEqual(
            PackageFormatter().format(
                'package name is {name}',
                Package(name='foo && $(bar) `date` "<>" \'<>\'')
            ),
            'package name is foo && $(bar) `date` "<>" \'<>\''
        )
        self.assertEqual(
            PackageFormatter(escape_mode='url').format(
                'http://example.com/{name}',
                Package(name='foo && $(bar) `date` "<>" \'<>\'')
            ),
            'http://example.com/foo%20%26%26%20%24%28bar%29%20%60date%60%20%22%3C%3E%22%20%27%3C%3E%27'
        )
        self.assertEqual(
            PackageFormatter(escape_mode='shell').format(
                'echo {name}',
                Package(name='foo && $(bar) `date` "<>" \'<>\'')
            ),
            """echo 'foo && $(bar) `date` "<>" '"'"'<>'"'"''"""
            # What we'd actually prefer is something more like:
            # 'echo foo\ \&\& \$\(bar\)\ \`date\`\ \"\<\>\"\ \'\<\>\''
        )


if __name__ == '__main__':
    unittest.main()
