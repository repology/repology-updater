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
        self.packages = repoman.ParseMulti(reponames=['freebsd', 'gentoo', 'arch'])

    def FindPackage(self, name):
        for package in self.packages:
            if package.name == name:
                return package

        return Package()

    def test_freebsd(self):
        p = self.FindPackage("vorbis-tools")
        self.assertEqual(p.repo, "freebsd")
        self.assertEqual(p.family, "freebsd")
        self.assertEqual(p.name, "vorbis-tools")
        self.assertEqual(p.version, "1.4.0")
        self.assertEqual(p.origversion, "1.4.0_10,3")
        self.assertEqual(p.category, "audio")
        self.assertEqual(p.comment, "Play, encode, and manage Ogg Vorbis files")
        self.assertEqual(p.maintainers, ['naddy@freebsd.org'])
        self.assertEqual(p.homepage, 'http://www.vorbis.com/')

    def test_gentoo(self):
        p = self.FindPackage("chromium-bsu")
        self.assertEqual(p.repo, "gentoo")
        self.assertEqual(p.family, "gentoo")
        self.assertEqual(p.name, "chromium-bsu")
        self.assertEqual(p.version, "0.9.15.1")
        self.assertEqual(p.origversion, None)
        self.assertEqual(p.category, "games-action")
        #self.assertEqual(p.comment, "Chromium B.S.U. - an arcade game")
        self.assertEqual(p.maintainers, ['games@gentoo.org'])
        #self.assertEqual(p.homepage, 'http://chromium-bsu.sourceforge.net/')

    def test_arch(self):
        p = self.FindPackage("zlib")
        self.assertEqual(p.repo, "arch")
        self.assertEqual(p.family, "arch")
        self.assertEqual(p.name, "zlib")
        self.assertEqual(p.version, "1.2.8")
        self.assertEqual(p.origversion, "1:1.2.8-7")
        self.assertEqual(p.comment, "Compression library implementing the deflate compression method found in gzip and PKZIP")
        self.assertEqual(p.homepage, "http://www.zlib.net/")
        self.assertEqual(p.licenses, ['custom'])
        self.assertEqual(p.maintainers, ['pierre@archlinux.de'])

if __name__ == '__main__':
    unittest.main()
