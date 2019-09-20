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
from typing import Any, Dict

from repology.config import config
from repology.repomgr import RepositoryManager
from repology.repoproc import RepositoryProcessor


repomgr = RepositoryManager(config['REPOS_DIR'])
repoproc = RepositoryProcessor(repomgr, 'testdata', 'testdata', safety_checks=False)


class TestParsers(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None
        self.packages = list(repoproc.iter_parse(reponames=['have_testdata']))

    def check_package(self, name: str, reference: Dict[str, Any]) -> None:
        reference_with_default: Dict[str, Any] = {
            # repo must be filled
            # family must be filled
            'subrepo': None,

            # name must be filled
            # visiblename must be filled
            # proectname_seed must be filled
            'basename': None,
            'keyname': None,

            # version must be filled
            # origversion must be filled
            # rawversion must be filled

            'arch': None,

            'maintainers': [],
            'category': None,
            'comment': None,
            'homepage': None,
            'licenses': [],
            'downloads': [],

            'flags': 0,
            'shadow': False,

            'flavors': [],

            'extrafields': {},
        }

        # not relevant here
        ignored_fields = [
            'effname',
            'versionclass',
        ]

        reference_with_default.update(reference)

        def sort_lists(what: Dict[str, Any]) -> Dict[str, Any]:
            output = {}
            for key, value in what.items():
                if isinstance(value, list):
                    output[key] = sorted(value)
                else:
                    output[key] = value

            return output

        for package in self.packages:
            if package.name == name:
                actual_fields = package.__dict__
                for field in ignored_fields:
                    actual_fields.pop(field, None)

                self.assertEqual(
                    sort_lists(actual_fields),
                    sort_lists(reference_with_default)
                )
                return

        self.assertFalse('package not found')

    def test_freebsd(self) -> None:
        self.check_package(
            'vorbis-tools',
            {
                'repo': 'freebsd',
                'family': 'freebsd',
                'name': 'vorbis-tools',
                'keyname': 'audio/vorbis-tools',
                'visiblename': 'audio/vorbis-tools',
                'projectname_seed': 'vorbis-tools',
                'version': '1.4.0',
                'origversion': '1.4.0',
                'rawversion': '1.4.0_10,3',
                'category': 'audio',
                'comment': 'Play, encode, and manage Ogg Vorbis files',
                'maintainers': ['naddy@freebsd.org'],
                'homepage': 'http://www.vorbis.com/',
            }
        )

    def test_gentoo(self) -> None:
        self.check_package(
            'chromium-bsu',
            {
                'repo': 'gentoo',
                'family': 'gentoo',
                'name': 'chromium-bsu',
                'visiblename': 'chromium-bsu',
                'projectname_seed': 'chromium-bsu',
                'version': '0.9.15.1',
                'origversion': '0.9.15.1',
                'rawversion': '0.9.15.1',
                'category': 'games-action',
                'maintainers': ['games@gentoo.org'],
                'homepage': 'http://chromium-bsu.sourceforge.net/',
                'comment': 'Chromium B.S.U. - an arcade game',
                'downloads': ['mirror://sourceforge/chromium-bsu/chromium-bsu-0.9.15.1.tar.gz'],
                'licenses': ['Clarified-Artistic'],
            }
        )
        self.check_package(
            'asciinema',
            {
                'repo': 'gentoo',
                'family': 'gentoo',
                'name': 'asciinema',
                'visiblename': 'asciinema',
                'projectname_seed': 'asciinema',
                'version': '1.3.0',
                'origversion': '1.3.0',
                'rawversion': '1.3.0',
                'category': 'app-misc',
                'maintainers': ['kensington@gentoo.org'],
                'homepage': 'https://asciinema.org/',  # ['https://asciinema.org/', 'https://pypi.python.org/pypi/asciinema']
                'comment': 'Command line recorder for asciinema.org service',
                'downloads': ['https://github.com/asciinema/asciinema/archive/v1.3.0.tar.gz'],
                'licenses': ['GPL-3+'],
            }
        )
        self.check_package(
            'away',
            {
                'repo': 'gentoo',
                'family': 'gentoo',
                'name': 'away',
                'visiblename': 'away',
                'projectname_seed': 'away',
                'version': '0.9.5',
                'origversion': '0.9.5',
                'rawversion': '0.9.5-r1',
                'category': 'app-misc',
                'maintainers': ['maintainer-needed@gentoo.org'],  # note this is generated by repomgr form repo config
                'homepage': 'http://unbeatenpath.net/software/away/',
                'comment': 'Terminal locking program with few additional features',
                'downloads': ['http://unbeatenpath.net/software/away/away-0.9.5.tar.bz2'],
                'licenses': ['GPL-2'],
            }
        )
        self.check_package(
            'aspell',
            {
                'repo': 'gentoo',
                'family': 'gentoo',
                'name': 'aspell',
                'visiblename': 'aspell',
                'projectname_seed': 'aspell',
                'version': '0.60.7_rc1',
                'origversion': '0.60.7_rc1',
                'rawversion': '0.60.7_rc1',
                'category': 'app-test',
                'maintainers': ['maintainer-needed@gentoo.org'],  # note this is generated by repomgr form repo config
                'homepage': 'http://aspell.net/',
                'comment': 'A spell checker replacement for ispell',
                'downloads': ['mirror://gnu-alpha/aspell/aspell-0.60.7-rc1.tar.gz'],
                'licenses': ['LGPL-2'],
            }
        )

    def test_arch(self) -> None:
        self.check_package(
            'zlib',
            {
                'repo': 'arch',
                'family': 'arch',
                'subrepo': 'core',
                'name': 'zlib',
                'basename': 'zlib',
                'visiblename': 'zlib',
                'projectname_seed': 'zlib',
                'version': '1.2.8',
                'origversion': '1.2.8',
                'rawversion': '1:1.2.8-7',
                'arch': None,
                'comment': 'Compression library implementing the deflate compression method found in gzip and PKZIP',
                'homepage': 'http://www.zlib.net/',
                'licenses': ['custom'],
                'maintainers': [],
                'extrafields': {'base': 'zlib'},
            }
        )

    def test_cpan(self) -> None:
        self.check_package(
            'Acme-Brainfuck',
            {
                'repo': 'cpan',
                'family': 'cpan',
                'name': 'Acme-Brainfuck',
                'visiblename': 'Acme-Brainfuck',
                'projectname_seed': 'Acme-Brainfuck',
                'version': '1.1.1',
                'origversion': '1.1.1',
                'rawversion': '1.1.1',
                'maintainers': ['jaldhar@cpan'],
                'homepage': 'http://search.cpan.org/dist/Acme-Brainfuck/',
                'shadow': True,
            }
        )

    def test_debian(self) -> None:
        self.check_package(
            'a52dec',
            {
                'repo': 'debian_unstable',
                'subrepo': 'main',
                'category': 'devel',
                'family': 'debuntu',
                'name': 'a52dec',
                'visiblename': 'a52dec',
                'projectname_seed': 'a52dec',
                'version': '0.7.4',
                'origversion': '0.7.4',
                'rawversion': '0.7.4-18',
                'maintainers': [
                    'pkg-multimedia-maintainers@lists.alioth.debian.org',
                    'dmitrij.ledkov@ubuntu.com',
                    'sam+deb@zoy.org',
                    'siretart@tauware.de',
                ],
                'homepage': 'http://liba52.sourceforge.net/',
            }
        )

    def test_gobolinux(self) -> None:
        self.check_package(
            'AutoFS',
            {
                'repo': 'gobolinux',
                'family': 'gobolinux',
                'name': 'AutoFS',
                'visiblename': 'AutoFS',
                'projectname_seed': 'AutoFS',
                'version': '5.0.5',
                'origversion': '5.0.5',
                'rawversion': '5.0.5',
                'comment': 'Automounting daemon',
                'homepage': 'ftp://ftp.kernel.org/pub/linux/daemons/autofs/',
                'downloads': [
                    'http://www.kernel.org/pub/linux/daemons/autofs/v5/autofs-5.0.5.tar.bz2'
                ],
                'licenses': ['GNU General Public License (GPL)'],
                'maintainers': []  # note this is generated by repomgr
            }
        )

    def test_slackbuilds(self) -> None:
        # multiline DOWNLOAD
        self.check_package(
            'virtualbox',
            {
                'repo': 'slackbuilds',
                'family': 'slackbuilds',
                'name': 'virtualbox',
                'visiblename': 'virtualbox',
                'projectname_seed': 'virtualbox',
                'version': '5.0.30',
                'origversion': '5.0.30',
                'rawversion': '5.0.30',
                'category': 'system',
                'homepage': 'http://www.virtualbox.org/',
                'downloads': [
                    'http://download.virtualbox.org/virtualbox/5.0.30/SDKRef.pdf',
                    'http://download.virtualbox.org/virtualbox/5.0.30/UserManual.pdf',
                    'http://download.virtualbox.org/virtualbox/5.0.30/VBoxGuestAdditions_5.0.30.iso',
                    'http://download.virtualbox.org/virtualbox/5.0.30/VirtualBox-5.0.30.tar.bz2',
                ],
                'maintainers': ['pprkut@liwjatan.at'],
            }
        )
        # different DOWNLOAD and DOWNLOAD_x86_64
        self.check_package(
            'baudline',
            {
                'repo': 'slackbuilds',
                'family': 'slackbuilds',
                'name': 'baudline',
                'visiblename': 'baudline',
                'projectname_seed': 'baudline',
                'version': '1.08',
                'origversion': '1.08',
                'rawversion': '1.08',
                'category': 'ham',
                'homepage': 'http://www.baudline.com/',
                'downloads': [
                    'http://www.baudline.com/baudline_1.08_linux_i686.tar.gz',
                    'http://www.baudline.com/baudline_1.08_linux_x86_64.tar.gz',
                ],
                'maintainers': ['joshuakwood@gmail.com'],
            }
        )
        # DOWNLOAD_x86_64 is UNSUPPORTED
        self.check_package(
            'teamviewer',
            {
                'repo': 'slackbuilds',
                'family': 'slackbuilds',
                'name': 'teamviewer',
                'visiblename': 'teamviewer',
                'projectname_seed': 'teamviewer',
                'version': '12.0.76279',
                'origversion': '12.0.76279',
                'rawversion': '12.0.76279',
                'category': 'network',
                'homepage': 'https://www.teamviewer.com/',
                'downloads': [
                    'https://download.teamviewer.com/download/teamviewer_i386.deb',
                ],
                'maintainers': ['willysr@slackbuilds.org'],
            }
        )
        # DOWNLOAD is UNSUPPORTED
        self.check_package(
            'oracle-xe',
            {
                'repo': 'slackbuilds',
                'family': 'slackbuilds',
                'name': 'oracle-xe',
                'visiblename': 'oracle-xe',
                'projectname_seed': 'oracle-xe',
                'version': '11.2.0',
                'origversion': '11.2.0',
                'rawversion': '11.2.0',
                'category': 'system',
                'homepage': 'http://www.oracle.com/technetwork/database/database-technologies/express-edition/overview/index.html',
                'downloads': [
                    'http://download.oracle.com/otn/linux/oracle11g/xe/oracle-xe-11.2.0-1.0.x86_64.rpm.zip',
                ],
                'maintainers': ['slack.dhabyx@gmail.com'],
            }
        )
        # DOWNLOAD_x86_64 is UNTESTED
        self.check_package(
            'kforth',
            {
                'repo': 'slackbuilds',
                'family': 'slackbuilds',
                'name': 'kforth',
                'visiblename': 'kforth',
                'projectname_seed': 'kforth',
                'version': '1.5.2p1',
                'origversion': '1.5.2p1',
                'rawversion': '1.5.2p1',
                'category': 'development',
                'homepage': 'http://ccreweb.org/software/kforth/kforth.html',
                'downloads': [
                    'ftp://ccreweb.org/software/kforth/linux/kforth-x86-linux-1.5.2.tar.gz',
                ],
                'maintainers': ['gschoen@iinet.net.au'],
            }
        )


if __name__ == '__main__':
    unittest.main()
