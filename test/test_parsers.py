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

from repology.repoman import RepositoryManager
from repology.package import Package


class TestParsers(unittest.TestCase):
    def setUp(self):
        repoman = RepositoryManager("testdata")
        self.packages = repoman.ParseMulti(reponames=['freebsd'])

    def FindPackage(self, name):
        for package in self.packages:
            if package.name == name:
                return package

        return Package()

    def test_freebsd(self):
        p = self.FindPackage("kiconvtool")
        self.assertEqual(p.name, "kiconvtool")
        self.assertEqual(p.version, "0.97")
        self.assertEqual(p.origversion, None)
        self.assertEqual(p.category, "sysutils")
        self.assertEqual(p.comment, "Tool to preload kernel iconv charset tables")
        self.assertEqual(p.maintainers, ['amdmi3@FreeBSD.org'])
        self.assertEqual(p.homepage, 'http://wiki.freebsd.org/DmitryMarakasov/kiconvtool')


if __name__ == '__main__':
    unittest.main()
