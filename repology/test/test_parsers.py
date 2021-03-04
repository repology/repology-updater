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
from repology.package import LinkType
from repology.repomgr import RepositoryManager
from repology.repoproc import RepositoryProcessor


repomgr = RepositoryManager(config['REPOS_DIR'])
repoproc = RepositoryProcessor(repomgr, 'testdata', 'testdata', safety_checks=False)


class TestParsers(unittest.TestCase):
    def setUp(self) -> None:
        self.maxDiff = None
        self.packages = list(repoproc.iter_parse(reponames=['have_testdata']))

    def check_package(self, reference: Dict[str, Any]) -> None:
        reference_with_default: Dict[str, Any] = {
            # repo must be filled
            # family must be filled
            'subrepo': None,

            'name': None,
            'srcname': None,
            'binname': None,
            'binnames': None,
            # trackname must be filled
            # visiblename must be filled
            # proectname_seed must be filled

            # version must be filled
            # origversion must be filled
            # rawversion must be filled

            'arch': None,

            'maintainers': None,
            'category': None,
            'comment': None,
            'licenses': None,

            'flags': 0,
            'shadow': False,

            'flavors': [],
            'branch': None,

            'extrafields': None,

            'cpe_vendor': None,
            'cpe_product': None,
            'cpe_edition': None,
            'cpe_lang': None,
            'cpe_sw_edition': None,
            'cpe_target_sw': None,
            'cpe_target_hw': None,
            'cpe_other': None,

            'links': None,
        }

        # not relevant here
        ignored_fields = [
            'effname',
            'versionclass',
        ]

        def normalize_fields(what: Dict[str, Any]) -> Dict[str, Any]:
            output = {}
            for key, value in what.items():
                if key in ignored_fields:
                    pass
                elif isinstance(value, list):
                    output[key] = sorted(value)
                else:
                    output[key] = value

            return output

        reference_with_default.update(reference)
        reference_with_default = normalize_fields(reference_with_default)

        best_match = None
        best_match_score = 0

        for package in self.packages:
            actual_fields = normalize_fields(package.__dict__)

            score = sum(1 for key in actual_fields.keys() if reference_with_default[key] == actual_fields[key])

            if score > best_match_score:
                best_match_score = score
                best_match = package

        if best_match is None:
            self.assertFalse('package not found')

        self.assertEqual(normalize_fields(best_match.__dict__), reference_with_default)

    def test_freebsd(self) -> None:
        self.check_package(
            {
                'repo': 'freebsd',
                'family': 'freebsd',
                'srcname': 'audio/vorbis-tools',
                'binname': 'vorbis-tools',
                'trackname': 'audio/vorbis-tools',
                'visiblename': 'audio/vorbis-tools',
                'projectname_seed': 'vorbis-tools',
                'version': '1.4.0',
                'origversion': '1.4.0',
                'rawversion': '1.4.0_10,3',
                'category': 'audio',
                'comment': 'Play, encode, and manage Ogg Vorbis files',
                'maintainers': ['naddy@freebsd.org'],
                'links': [
                    (LinkType.UPSTREAM_HOMEPAGE, 'http://www.vorbis.com/'),
                    (LinkType.PACKAGE_HOMEPAGE, 'https://www.freshports.org/audio/vorbis-tools'),
                    (LinkType.PACKAGE_REPOSITORY_DIR, 'https://svnweb.freebsd.org/ports/head/audio/vorbis-tools/'),
                    (LinkType.PACKAGE_RECIPE_RAW, 'https://svnweb.freebsd.org/ports/head/audio/vorbis-tools/Makefile?view=co'),
                    (LinkType.PACKAGE_ISSUE_TRACKER, 'https://bugs.freebsd.org/bugzilla/buglist.cgi?quicksearch=audio/vorbis-tools'),
                ],
            }
        )

    def test_gentoo(self) -> None:
        self.check_package(
            {
                'repo': 'gentoo',
                'family': 'gentoo',
                'srcname': 'games-action/chromium-bsu',
                'trackname': 'games-action/chromium-bsu',
                'visiblename': 'games-action/chromium-bsu',
                'projectname_seed': 'chromium-bsu',
                'version': '0.9.15.1',
                'origversion': '0.9.15.1',
                'rawversion': '0.9.15.1',
                'category': 'games-action',
                'maintainers': ['games@gentoo.org'],
                'comment': 'Chromium B.S.U. - an arcade game',
                'licenses': ['Clarified-Artistic'],
                'links': [
                    (LinkType.UPSTREAM_HOMEPAGE, 'http://chromium-bsu.sourceforge.net/'),
                    (LinkType.UPSTREAM_HOMEPAGE, 'https://sourceforge.net/projects/chromium-bsu/'),
                    (LinkType.UPSTREAM_DOWNLOAD, 'mirror://sourceforge/chromium-bsu/chromium-bsu-0.9.15.1.tar.gz'),
                    (LinkType.PACKAGE_HOMEPAGE, 'https://packages.gentoo.org/packages/games-action/chromium-bsu'),
                    (LinkType.PACKAGE_REPOSITORY_DIR, 'https://gitweb.gentoo.org/repo/gentoo.git/tree/games-action/chromium-bsu'),
                    (LinkType.PACKAGE_RECIPE, 'https://gitweb.gentoo.org/repo/gentoo.git/tree/games-action/chromium-bsu/chromium-bsu-0.9.15.1.ebuild'),
                    (LinkType.PACKAGE_RECIPE_RAW, 'https://gitweb.gentoo.org/repo/gentoo.git/plain/games-action/chromium-bsu/chromium-bsu-0.9.15.1.ebuild'),
                ],
            }
        )
        self.check_package(
            {
                'repo': 'gentoo',
                'family': 'gentoo',
                'srcname': 'app-misc/asciinema',
                'trackname': 'app-misc/asciinema',
                'visiblename': 'app-misc/asciinema',
                'projectname_seed': 'asciinema',
                'version': '1.3.0',
                'origversion': '1.3.0',
                'rawversion': '1.3.0',
                'category': 'app-misc',
                'maintainers': ['kensington@gentoo.org'],
                'comment': 'Command line recorder for asciinema.org service',
                'licenses': ['GPL-3+'],
                'links': [
                    (LinkType.UPSTREAM_HOMEPAGE, 'https://asciinema.org/'),
                    (LinkType.UPSTREAM_HOMEPAGE, 'https://github.com/asciinema/asciinema'),
                    (LinkType.UPSTREAM_HOMEPAGE, 'https://pypi.org/project/asciinema/'),
                    (LinkType.UPSTREAM_HOMEPAGE, 'https://pypi.python.org/pypi/asciinema'),
                    (LinkType.UPSTREAM_DOWNLOAD, 'https://github.com/asciinema/asciinema/archive/v1.3.0.tar.gz'),
                    (LinkType.PACKAGE_HOMEPAGE, 'https://packages.gentoo.org/packages/app-misc/asciinema'),
                    (LinkType.PACKAGE_REPOSITORY_DIR, 'https://gitweb.gentoo.org/repo/gentoo.git/tree/app-misc/asciinema'),
                    (LinkType.PACKAGE_RECIPE, 'https://gitweb.gentoo.org/repo/gentoo.git/tree/app-misc/asciinema/asciinema-1.3.0.ebuild'),
                    (LinkType.PACKAGE_RECIPE_RAW, 'https://gitweb.gentoo.org/repo/gentoo.git/plain/app-misc/asciinema/asciinema-1.3.0.ebuild'),
                ],
            }
        )
        self.check_package(
            {
                'repo': 'gentoo',
                'family': 'gentoo',
                'srcname': 'app-misc/away',
                'trackname': 'app-misc/away',
                'visiblename': 'app-misc/away',
                'projectname_seed': 'away',
                'version': '0.9.5',
                'origversion': '0.9.5',
                'rawversion': '0.9.5-r1',
                'category': 'app-misc',
                'maintainers': ['maintainer-needed@gentoo.org'],  # note this is generated by repomgr form repo config
                'comment': 'Terminal locking program with few additional features',
                'licenses': ['GPL-2'],
                'links': [
                    (LinkType.UPSTREAM_HOMEPAGE, 'http://unbeatenpath.net/software/away/'),
                    (LinkType.UPSTREAM_DOWNLOAD, 'http://unbeatenpath.net/software/away/away-0.9.5.tar.bz2'),
                    (LinkType.PACKAGE_HOMEPAGE, 'https://packages.gentoo.org/packages/app-misc/away'),
                    (LinkType.PACKAGE_REPOSITORY_DIR, 'https://gitweb.gentoo.org/repo/gentoo.git/tree/app-misc/away'),
                    (LinkType.PACKAGE_RECIPE, 'https://gitweb.gentoo.org/repo/gentoo.git/tree/app-misc/away/away-0.9.5-r1.ebuild'),
                    (LinkType.PACKAGE_RECIPE_RAW, 'https://gitweb.gentoo.org/repo/gentoo.git/plain/app-misc/away/away-0.9.5-r1.ebuild'),
                ],
            }
        )
        self.check_package(
            {
                'repo': 'gentoo',
                'family': 'gentoo',
                'srcname': 'app-test/aspell',
                'trackname': 'app-test/aspell',
                'visiblename': 'app-test/aspell',
                'projectname_seed': 'aspell',
                'version': '0.60.7_rc1',
                'origversion': '0.60.7_rc1',
                'rawversion': '0.60.7_rc1',
                'category': 'app-test',
                'maintainers': ['maintainer-needed@gentoo.org'],  # note this is generated by repomgr form repo config
                'comment': 'A spell checker replacement for ispell',
                'licenses': ['LGPL-2'],
                'links': [
                    (LinkType.UPSTREAM_HOMEPAGE, 'http://aspell.net/'),
                    (LinkType.UPSTREAM_DOWNLOAD, 'mirror://gnu-alpha/aspell/aspell-0.60.7-rc1.tar.gz'),
                    (LinkType.PACKAGE_HOMEPAGE, 'https://packages.gentoo.org/packages/app-test/aspell'),
                    (LinkType.PACKAGE_REPOSITORY_DIR, 'https://gitweb.gentoo.org/repo/gentoo.git/tree/app-test/aspell'),
                    (LinkType.PACKAGE_RECIPE, 'https://gitweb.gentoo.org/repo/gentoo.git/tree/app-test/aspell/aspell-0.60.7_rc1.ebuild'),
                    (LinkType.PACKAGE_RECIPE_RAW, 'https://gitweb.gentoo.org/repo/gentoo.git/plain/app-test/aspell/aspell-0.60.7_rc1.ebuild'),
                ],
            }
        )

    def test_arch(self) -> None:
        self.check_package(
            {
                'repo': 'arch',
                'family': 'arch',
                'subrepo': 'core',
                'srcname': 'zlib',
                'binname': 'zlib',
                'trackname': 'zlib',
                'visiblename': 'zlib',
                'projectname_seed': 'zlib',
                'version': '1.2.8',
                'origversion': '1.2.8',
                'rawversion': '1:1.2.8-7',
                'arch': None,
                'comment': 'Compression library implementing the deflate compression method found in gzip and PKZIP',
                'licenses': ['custom'],
                'maintainers': None,
                'links': [
                    (LinkType.UPSTREAM_HOMEPAGE, 'http://www.zlib.net/'),
                ],
            }
        )

    def test_cpan(self) -> None:
        self.check_package(
            {
                'repo': 'cpan',
                'family': 'cpan',
                'name': 'Acme-Brainfuck',
                'trackname': 'Acme-Brainfuck',
                'visiblename': 'Acme-Brainfuck',
                'projectname_seed': 'Acme-Brainfuck',
                'version': '1.1.1',
                'origversion': '1.1.1',
                'rawversion': '1.1.1',
                'maintainers': ['jaldhar@cpan'],
                'shadow': True,
                'links': [
                    (LinkType.UPSTREAM_HOMEPAGE, 'http://search.cpan.org/dist/Acme-Brainfuck/'),
                ],
            }
        )

    def test_debian(self) -> None:
        self.check_package(
            {
                'repo': 'debian_unstable',
                'subrepo': 'main',
                'category': 'devel',
                'family': 'debuntu',
                'srcname': 'a52dec',
                'binnames': ['liba52-0.7.4', 'liba52-0.7.4-dev'],
                'trackname': 'a52dec',
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
                'links': [
                    (LinkType.UPSTREAM_HOMEPAGE, 'http://liba52.sourceforge.net/'),
                ],
            }
        )

    def test_gobolinux(self) -> None:
        self.check_package(
            {
                'repo': 'gobolinux',
                'family': 'gobolinux',
                'name': 'AutoFS',
                'trackname': 'AutoFS',
                'visiblename': 'AutoFS',
                'projectname_seed': 'AutoFS',
                'version': '5.0.5',
                'origversion': '5.0.5',
                'rawversion': '5.0.5',
                'comment': 'Automounting daemon',
                'licenses': ['GNU General Public License (GPL)'],
                'maintainers': None,  # note this is generated by repomgr
                'extrafields': {'patch': ['10-dont_install_initfile.patch', '30-default_master_map_location.patch']},
                'links': [
                    (LinkType.UPSTREAM_HOMEPAGE, 'ftp://ftp.kernel.org/pub/linux/daemons/autofs/'),
                    (LinkType.UPSTREAM_DOWNLOAD, 'http://www.kernel.org/pub/linux/daemons/autofs/v5/autofs-5.0.5.tar.bz2'),
                    (LinkType.PACKAGE_REPOSITORY_DIR, 'https://github.com/gobolinux/Recipes/tree/master/AutoFS/5.0.5'),
                    (LinkType.PACKAGE_RECIPE, 'https://github.com/gobolinux/Recipes/blob/master/AutoFS/5.0.5/Recipe'),
                    (LinkType.PACKAGE_RECIPE_RAW, 'https://raw.githubusercontent.com/gobolinux/Recipes/master/AutoFS/5.0.5/Recipe'),
                    (LinkType.PACKAGE_PATCH, 'https://github.com/gobolinux/Recipes/blob/master/AutoFS/5.0.5/10-dont_install_initfile.patch'),
                    (LinkType.PACKAGE_PATCH, 'https://github.com/gobolinux/Recipes/blob/master/AutoFS/5.0.5/30-default_master_map_location.patch'),
                    (LinkType.PACKAGE_PATCH_RAW, 'https://raw.githubusercontent.com/gobolinux/Recipes/master/AutoFS/5.0.5/10-dont_install_initfile.patch'),
                    (LinkType.PACKAGE_PATCH_RAW, 'https://raw.githubusercontent.com/gobolinux/Recipes/master/AutoFS/5.0.5/30-default_master_map_location.patch',),
                ],
            }
        )

    def test_slackbuilds(self) -> None:
        # multiline DOWNLOAD
        self.check_package(
            {
                'repo': 'slackbuilds',
                'family': 'slackbuilds',
                'srcname': 'system/virtualbox',
                'trackname': 'system/virtualbox',
                'visiblename': 'system/virtualbox',
                'projectname_seed': 'virtualbox',
                'version': '5.0.30',
                'origversion': '5.0.30',
                'rawversion': '5.0.30',
                'category': 'system',
                'maintainers': ['pprkut@liwjatan.at'],
                'links': [
                    (LinkType.UPSTREAM_HOMEPAGE, 'http://www.virtualbox.org/'),
                    (LinkType.UPSTREAM_DOWNLOAD, 'http://download.virtualbox.org/virtualbox/5.0.30/SDKRef.pdf'),
                    (LinkType.UPSTREAM_DOWNLOAD, 'http://download.virtualbox.org/virtualbox/5.0.30/UserManual.pdf'),
                    (LinkType.UPSTREAM_DOWNLOAD, 'http://download.virtualbox.org/virtualbox/5.0.30/VBoxGuestAdditions_5.0.30.iso'),
                    (LinkType.UPSTREAM_DOWNLOAD, 'http://download.virtualbox.org/virtualbox/5.0.30/VirtualBox-5.0.30.tar.bz2'),
                    (LinkType.PACKAGE_HOMEPAGE, 'https://slackbuilds.org/repository/14.2/system/virtualbox/'),
                    (LinkType.PACKAGE_RECIPE_RAW, 'https://slackbuilds.org/slackbuilds/14.2/system/virtualbox/virtualbox.SlackBuild'),
                ],
            }
        )
        # different DOWNLOAD and DOWNLOAD_x86_64
        self.check_package(
            {
                'repo': 'slackbuilds',
                'family': 'slackbuilds',
                'srcname': 'ham/baudline',
                'trackname': 'ham/baudline',
                'visiblename': 'ham/baudline',
                'projectname_seed': 'baudline',
                'version': '1.08',
                'origversion': '1.08',
                'rawversion': '1.08',
                'category': 'ham',
                'maintainers': ['joshuakwood@gmail.com'],
                'links': [
                    (LinkType.UPSTREAM_HOMEPAGE, 'http://www.baudline.com/'),
                    (LinkType.UPSTREAM_DOWNLOAD, 'http://www.baudline.com/baudline_1.08_linux_i686.tar.gz'),
                    (LinkType.UPSTREAM_DOWNLOAD, 'http://www.baudline.com/baudline_1.08_linux_x86_64.tar.gz'),
                    (LinkType.PACKAGE_HOMEPAGE, 'https://slackbuilds.org/repository/14.2/ham/baudline/'),
                    (LinkType.PACKAGE_RECIPE_RAW, 'https://slackbuilds.org/slackbuilds/14.2/ham/baudline/baudline.SlackBuild'),
                ],
            }
        )
        # DOWNLOAD_x86_64 is UNSUPPORTED
        self.check_package(
            {
                'repo': 'slackbuilds',
                'family': 'slackbuilds',
                'srcname': 'network/teamviewer',
                'trackname': 'network/teamviewer',
                'visiblename': 'network/teamviewer',
                'projectname_seed': 'teamviewer',
                'version': '12.0.76279',
                'origversion': '12.0.76279',
                'rawversion': '12.0.76279',
                'category': 'network',
                'maintainers': ['willysr@slackbuilds.org'],
                'links': [
                    (LinkType.UPSTREAM_HOMEPAGE, 'https://www.teamviewer.com/'),
                    (LinkType.UPSTREAM_DOWNLOAD, 'https://download.teamviewer.com/download/teamviewer_i386.deb'),
                    (LinkType.PACKAGE_HOMEPAGE, 'https://slackbuilds.org/repository/14.2/network/teamviewer/'),
                    (LinkType.PACKAGE_RECIPE_RAW, 'https://slackbuilds.org/slackbuilds/14.2/network/teamviewer/teamviewer.SlackBuild'),
                ],
            }
        )
        # DOWNLOAD is UNSUPPORTED
        self.check_package(
            {
                'repo': 'slackbuilds',
                'family': 'slackbuilds',
                'srcname': 'system/oracle-xe',
                'trackname': 'system/oracle-xe',
                'visiblename': 'system/oracle-xe',
                'projectname_seed': 'oracle-xe',
                'version': '11.2.0',
                'origversion': '11.2.0',
                'rawversion': '11.2.0',
                'category': 'system',
                'maintainers': ['slack.dhabyx@gmail.com'],
                'links': [
                    (LinkType.UPSTREAM_HOMEPAGE, 'http://www.oracle.com/technetwork/database/database-technologies/express-edition/overview/index.html'),
                    (LinkType.UPSTREAM_DOWNLOAD, 'http://download.oracle.com/otn/linux/oracle11g/xe/oracle-xe-11.2.0-1.0.x86_64.rpm.zip'),
                    (LinkType.PACKAGE_HOMEPAGE, 'https://slackbuilds.org/repository/14.2/system/oracle-xe/'),
                    (LinkType.PACKAGE_RECIPE_RAW, 'https://slackbuilds.org/slackbuilds/14.2/system/oracle-xe/oracle-xe.SlackBuild'),
                ],
            }
        )
        # DOWNLOAD_x86_64 is UNTESTED
        self.check_package(
            {
                'repo': 'slackbuilds',
                'family': 'slackbuilds',
                'srcname': 'development/kforth',
                'trackname': 'development/kforth',
                'visiblename': 'development/kforth',
                'projectname_seed': 'kforth',
                'version': '1.5.2p1',
                'origversion': '1.5.2p1',
                'rawversion': '1.5.2p1',
                'category': 'development',
                'maintainers': ['gschoen@iinet.net.au'],
                'links': [
                    (LinkType.UPSTREAM_HOMEPAGE, 'http://ccreweb.org/software/kforth/kforth.html'),
                    (LinkType.UPSTREAM_DOWNLOAD, 'ftp://ccreweb.org/software/kforth/linux/kforth-x86-linux-1.5.2.tar.gz'),
                    (LinkType.PACKAGE_HOMEPAGE, 'https://slackbuilds.org/repository/14.2/development/kforth/'),
                    (LinkType.PACKAGE_RECIPE_RAW, 'https://slackbuilds.org/slackbuilds/14.2/development/kforth/kforth.SlackBuild'),
                ],
            }
        )


if __name__ == '__main__':
    unittest.main()
