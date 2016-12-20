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
        self.maxDiff = None
        repoman = RepositoryManager("testdata")
        self.packages = repoman.ParseMulti(reponames=['have_testdata'])

    def check_package(self, name, reference):
        reference_with_default = {
            # repo must be filled
            # family must be filled

            # name must be filled
            'effname': None,

            # version must be filled
            'origversion': None,
            'effversion': None,
            'versionclass': None,

            'maintainers': [],
            'category': None,
            'comment': None,
            'homepage': None,
            'licenses': [],
            'downloads': [],

            'ignore': False,
            'shadow': False,
            'ignoreversion': False,
        }

        reference_with_default.update(reference)

        def sort_lists(what):
            output = {}
            for key, value in what.items():
                if isinstance(value, list):
                    output[key] = sorted(value)
                else:
                    output[key] = value

            return output

        for package in self.packages:
            if package.name == name:
                self.assertEqual(
                    sort_lists(package.__dict__),
                    sort_lists(reference_with_default)
                )
                return

        self.assertFalse("package not found")

    def test_freebsd(self):
        self.check_package("vorbis-tools",
            {
                'repo': "freebsd",
                'family': "freebsd",
                'name': "vorbis-tools",
                'version': "1.4.0",
                'origversion': "1.4.0_10,3",
                'category': "audio",
                'comment': "Play, encode, and manage Ogg Vorbis files",
                'maintainers': ['naddy@freebsd.org'],
                'homepage': 'http://www.vorbis.com/',
            }
        )

    def test_gentoo(self):
        self.check_package("chromium-bsu",
            {
                "repo": "gentoo",
                "family": "gentoo",
                "name": "chromium-bsu",
                "version": "0.9.15.1",
                "origversion": None,
                "category": "games-action",
                "maintainers": ['games@gentoo.org'],
            }
        )

    def test_arch(self):
        self.check_package("zlib",
            {
                "repo": "arch",
                "family": "arch",
                "name": "zlib",
                "version": "1.2.8",
                "origversion": "1:1.2.8-7",
                "comment": "Compression library implementing the deflate compression method found in gzip and PKZIP",
                "homepage": "http://www.zlib.net/",
                "licenses": ['custom'],
                "maintainers": ['pierre@archlinux.de'],
            }
        )

    def test_cpan(self):
        self.check_package("Acme-Brainfuck",
            {
                "repo": "cpan",
                "family": "cpan",
                "name": "Acme-Brainfuck",
                "version": "1.1.1",
                "maintainers": ['jaldhar@cpan'],
                "homepage": "http://search.cpan.org/dist/Acme-Brainfuck/",
                "shadow": True,
            }
        )

    def test_debian(self):
        self.check_package("a52dec",
            {
                "repo": "debian_unstable",
                "category": "devel",
                "family": "debian",
                "name": "a52dec",
                "version": "0.7.4",
                "origversion": "0.7.4-18",
                "maintainers": [
                    'pkg-multimedia-maintainers@lists.alioth.debian.org',
                    'dmitrij.ledkov@ubuntu.com',
                    'sam+deb@zoy.org',
                    'siretart@tauware.de',
                ],
                "homepage": "http://liba52.sourceforge.net/",
            }
        )

if __name__ == '__main__':
    unittest.main()
