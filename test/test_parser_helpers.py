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

from repology.parsers.helpers.nevra import filename2nevra


class TestParserHelpers(unittest.TestCase):
    def test_filename2nevra(self):
        self.assertEqual(filename2nevra('foo-1.2.3-1.i386.rpm'), ('foo', '', '1.2.3', '1', 'i386'))
        self.assertEqual(filename2nevra('foo-bar-baz-999:1.2.3-1.src.rpm'), ('foo-bar-baz', '999', '1.2.3', '1', 'src'))


if __name__ == '__main__':
    unittest.main()
