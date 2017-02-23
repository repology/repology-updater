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

import repology.config


class TestParsers(unittest.TestCase):
    def setUp(self):
        self.maxDiff = None
        repoman = RepositoryManager(repology.config.REPOS_PATH, "testdata")
        self.packages = repoman.ParseMulti(reponames=['have_testdata'])

    def check_package(self, name, reference):
        reference_with_default = {
            # repo must be filled
            # family must be filled
            'subrepo': None,

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
                "homepage": 'http://chromium-bsu.sourceforge.net/',
                "comment": 'Chromium B.S.U. - an arcade game',
                "downloads": ['mirror://sourceforge/chromium-bsu/chromium-bsu-0.9.15.1.tar.gz'],
                "licenses": ['Clarified-Artistic'],
            }
        )
        self.check_package("asciinema",
            {
                "repo": "gentoo",
                "family": "gentoo",
                "name": "asciinema",
                "version": "1.3.0",
                "origversion": None,
                "category": "app-misc",
                "maintainers": ['kensington@gentoo.org'],
                "homepage": 'https://asciinema.org/', # ['https://asciinema.org/', 'https://pypi.python.org/pypi/asciinema']
                "comment": 'Command line recorder for asciinema.org service',
                "downloads": [],
                "licenses": ['GPL-3+'],
            }
        )
        self.check_package("away",
            {
                "repo": "gentoo",
                "family": "gentoo",
                "name": "away",
                "version": "0.9.5",
                "origversion": "0.9.5-r1",
                "category": "app-misc",
                "maintainers": ['maintainer-needed@gentoo.org'],
                "homepage": 'http://unbeatenpath.net/software/away/',
                "comment": 'Terminal locking program with few additional features',
                "downloads": ['http://unbeatenpath.net/software/away/away-0.9.5.tar.bz2'],
                "licenses": ['GPL-2'],
            }
        )

    def test_arch(self):
        self.check_package("zlib",
            {
                "repo": "arch",
                "family": "arch",
                "subrepo": "core",
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
                "subrepo": "main",
                "category": "devel",
                "family": "debuntu",
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

    def test_gobolinux(self):
        self.check_package("AutoFS",
            {
                "repo": "gobolinux",
                "family": "gobolinux",
                "name": "AutoFS",
                "version": "5.0.5",
                "comment": "Automounting daemon",
                "homepage": "ftp://ftp.kernel.org/pub/linux/daemons/autofs/",
                "downloads": [
                    "http://www.kernel.org/pub/linux/daemons/autofs/v5/autofs-5.0.5.tar.bz2"
                ],
                "licenses": ["GNU General Public License (GPL)"]
            }
        )

if __name__ == '__main__':
    unittest.main()
