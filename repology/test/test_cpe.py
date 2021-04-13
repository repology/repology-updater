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

from repology.parsers.cpe import cpe_parse


class TestCpe(unittest.TestCase):
    def test_cpe_parse(self) -> None:
        self.assertEqual(cpe_parse('foo:bar'), ['foo', 'bar'])
        self.assertEqual(cpe_parse('foobar'), ['foobar'])
        self.assertEqual(cpe_parse('cpe:2.3:a:andreas_mueller:cdrdao'), ['cpe', '2.3', 'a', 'andreas_mueller', 'cdrdao'])
        self.assertEqual(cpe_parse('cpe:/a:archive\\:\\:tar_project:archive\\:\\:tar'), ['cpe', '/a', 'archive\\:\\:tar_project', 'archive\\:\\:tar'])
        self.assertEqual(cpe_parse('foo\\:bar'), ['foo\\:bar'])
        self.assertEqual(cpe_parse('foo\\\\:bar'), ['foo\\\\', 'bar'])

    @unittest.expectedFailure
    def test_cpe_parse_failure(self) -> None:
        self.assertEqual(cpe_parse('a:b'), ['ab'])
        self.assertEqual(cpe_parse('foo\\:bar'), ['foo:bar'])
        self.assertEqual(cpe_parse('foo\\\\:bar'), ['foo', 'bar'])


if __name__ == '__main__':
    unittest.main()
