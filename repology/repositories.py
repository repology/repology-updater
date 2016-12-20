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

from repology.fetcher import *
from repology.parser import *


REPOSITORIES = [
    {
        'name': 'freebsd',
        'desc': "FreeBSD",
        'family': 'freebsd',
        'fetcher': lambda: FileFetcher("http://www.FreeBSD.org/ports/INDEX-11.bz2", bz2=True),
        'parser': lambda: FreeBSDIndexParser(),
        'link': 'http://www.freshports.org/{category}/{name}',
        'tags': ['all', 'have_testdata', 'demo', 'production', 'fastfetch'],
    },

    {
        'name': 'debian_stable',
        'desc': 'Debian Stable',
        'family': 'debian',
        'fetcher': lambda: FileFetcher(
            "http://ftp.debian.org/debian/dists/stable/contrib/source/Sources.gz",
            "http://ftp.debian.org/debian/dists/stable/main/source/Sources.gz",
            "http://ftp.debian.org/debian/dists/stable/non-free/source/Sources.gz",
            gz=True
        ),
        'parser': lambda: DebianSourcesParser(),
        'link': 'https://packages.debian.org/stable/{name}',
        'tags': ['all', 'debian', 'fastfetch'],
    },
    {
        'name': 'debian_stable_backports',
        'desc': 'Debian Stable Backports',
        'family': 'debian',
        'fetcher': lambda: FileFetcher(
            "http://ftp.debian.org/debian/dists/stable-backports/contrib/source/Sources.gz",
            "http://ftp.debian.org/debian/dists/stable-backports/main/source/Sources.gz",
            "http://ftp.debian.org/debian/dists/stable-backports/non-free/source/Sources.gz",
            gz=True
        ),
        'parser': lambda: DebianSourcesParser(),
        'link': 'https://packages.debian.org/stable-backports/{name}',
        'tags': ['all', 'debian', 'fastfetch'],
    },
    {
        'name': 'debian_testing',
        'desc': 'Debian Testing',
        'family': 'debian',
        'fetcher': lambda: FileFetcher(
            "http://ftp.debian.org/debian/dists/testing/contrib/source/Sources.gz",
            "http://ftp.debian.org/debian/dists/testing/main/source/Sources.gz",
            "http://ftp.debian.org/debian/dists/testing/non-free/source/Sources.gz",
            gz=True
        ),
        'parser': lambda: DebianSourcesParser(),
        'link': 'https://packages.debian.org/testing/{name}',
        'tags': ['all', 'debian', 'fastfetch'],
    },
    {
        'name': 'debian_unstable',
        'desc': 'Debian Unstable',
        'family': 'debian',
        'fetcher': lambda: FileFetcher(
            "http://ftp.debian.org/debian/dists/unstable/contrib/source/Sources.gz",
            "http://ftp.debian.org/debian/dists/unstable/main/source/Sources.gz",
            "http://ftp.debian.org/debian/dists/unstable/non-free/source/Sources.gz",
            gz=True
        ),
        'parser': lambda: DebianSourcesParser(),
        'link': 'https://packages.debian.org/unstable/{name}',
        'tags': ['all', 'have_testdata', 'demo', 'debian', 'production', 'fastfetch'],
    },
    {
        'name': 'debian_experimental',
        'desc': 'Debian Experimental',
        'family': 'debian',
        'fetcher': lambda: FileFetcher(
            "http://ftp.debian.org/debian/dists/experimental/contrib/source/Sources.xz",
            "http://ftp.debian.org/debian/dists/experimental/main/source/Sources.xz",
            "http://ftp.debian.org/debian/dists/experimental/non-free/source/Sources.xz",
            xz=True
        ),
        'parser': lambda: DebianSourcesParser(),
        'link': 'https://packages.debian.org/experimental/{name}',
        'tags': ['all', 'preproduction', 'debian', 'fastfetch'],
    },

    {
        'name': 'ubuntu_precise',
        'desc': 'Ubuntu Precise',
        'family': 'debian',
        'fetcher': lambda: FileFetcher(
            "http://ftp.ubuntu.com/ubuntu/dists/precise/main/source/Sources.gz",
            "http://ftp.ubuntu.com/ubuntu/dists/precise/multiverse/source/Sources.gz",
            "http://ftp.ubuntu.com/ubuntu/dists/precise/restricted/source/Sources.gz",
            "http://ftp.ubuntu.com/ubuntu/dists/precise/universe/source/Sources.gz",
            gz=True
        ),
        'parser': lambda: DebianSourcesParser(),
        'link': 'http://packages.ubuntu.com/precise/{name}',
        'tags': ['all', 'ubuntu', 'fastfetch'],
    },
    {
        'name': 'ubuntu_trusty',
        'desc': 'Ubuntu Trusty',
        'family': 'debian',
        'fetcher': lambda: FileFetcher(
            "http://ftp.ubuntu.com/ubuntu/dists/trusty/main/source/Sources.gz",
            "http://ftp.ubuntu.com/ubuntu/dists/trusty/multiverse/source/Sources.gz",
            "http://ftp.ubuntu.com/ubuntu/dists/trusty/restricted/source/Sources.gz",
            "http://ftp.ubuntu.com/ubuntu/dists/trusty/universe/source/Sources.gz",
            gz=True
        ),
        'parser': lambda: DebianSourcesParser(),
        'link': 'http://packages.ubuntu.com/trusty/{name}',
        'tags': ['all', 'ubuntu', 'fastfetch'],
    },
    {
        'name': 'ubuntu_xenial',
        'desc': 'Ubuntu Xenial',
        'family': 'debian',
        'fetcher': lambda: FileFetcher(
            "http://ftp.ubuntu.com/ubuntu/dists/xenial/main/source/Sources.gz",
            "http://ftp.ubuntu.com/ubuntu/dists/xenial/multiverse/source/Sources.gz",
            "http://ftp.ubuntu.com/ubuntu/dists/xenial/restricted/source/Sources.gz",
            "http://ftp.ubuntu.com/ubuntu/dists/xenial/universe/source/Sources.gz",
            gz=True
        ),
        'parser': lambda: DebianSourcesParser(),
        'link': 'http://packages.ubuntu.com/xenial/{name}',
        'tags': ['all', 'ubuntu', 'fastfetch'],
    },
    {
        'name': 'ubuntu_yakkety',
        'desc': 'Ubuntu Yakkety',
        'family': 'debian',
        'fetcher': lambda: FileFetcher(
            "http://ftp.ubuntu.com/ubuntu/dists/yakkety/main/source/Sources.gz",
            "http://ftp.ubuntu.com/ubuntu/dists/yakkety/multiverse/source/Sources.gz",
            "http://ftp.ubuntu.com/ubuntu/dists/yakkety/restricted/source/Sources.gz",
            "http://ftp.ubuntu.com/ubuntu/dists/yakkety/universe/source/Sources.gz",
            gz=True
        ),
        'parser': lambda: DebianSourcesParser(),
        'link': 'http://packages.ubuntu.com/yakkety/{name}',
        'tags': ['all', 'ubuntu', 'fastfetch'],
    },
    {
        'name': 'ubuntu_zesty',
        'desc': 'Ubuntu Zesty',
        'family': 'debian',
        'fetcher': lambda: FileFetcher(
            "http://ftp.ubuntu.com/ubuntu/dists/zesty/main/source/Sources.gz",
            "http://ftp.ubuntu.com/ubuntu/dists/zesty/multiverse/source/Sources.gz",
            "http://ftp.ubuntu.com/ubuntu/dists/zesty/restricted/source/Sources.gz",
            "http://ftp.ubuntu.com/ubuntu/dists/zesty/universe/source/Sources.gz",
            gz=True
        ),
        'parser': lambda: DebianSourcesParser(),
        'link': 'http://packages.ubuntu.com/zesty/{name}',
        'tags': ['all', 'demo', 'production', 'ubuntu', 'fastfetch'],
    },

    {
        'name': 'gentoo',
        'desc': 'Gentoo',
        'family': 'gentoo',
        'fetcher': lambda: GitFetcher("https://github.com/gentoo/gentoo.git"),
        'parser': lambda: GentooGitParser(),
        'link': 'https://packages.gentoo.org/packages/{category}/{name}',
        'tags': ['all', 'have_testdata', 'demo', 'production', 'fastfetch'],
    },
    {
        'name': 'pkgsrc',
        'desc': 'pkgsrc',
        'family': 'pkgsrc',
        'fetcher': lambda: FileFetcher("https://ftp.netbsd.org/pub/pkgsrc/current/pkgsrc/INDEX"),
        'parser': lambda: PkgsrcIndexParser(),
        'link': 'http://cvsweb.netbsd.org/bsdweb.cgi/pkgsrc/{category}/{name}',
        'tags': ['all', 'demo', 'production', 'fastfetch'],
    },
    {
        'name': 'openbsd',
        'desc': 'OpenBSD',
        'family': 'openbsd',
        'fetcher': lambda: FileFetcher("http://cvsweb.openbsd.org/cgi-bin/cvsweb/~checkout~/ports/INDEX?content-type=text/plain"),
        'parser': lambda: OpenBSDIndexParser(),
        'link': 'http://cvsweb.openbsd.org/cgi-bin/cvsweb/ports/{category}/{name}',
        'tags': ['all', 'demo', 'production', 'fastfetch'],
    },
    {
        'name': 'arch',
        'desc': 'Arch',
        'family': 'arch',
        'fetcher': lambda: ArchDBFetcher(
            "http://delta.archlinux.fr/core/os/x86_64/core.db.tar.gz",
            "http://delta.archlinux.fr/extra/os/x86_64/extra.db.tar.gz",
            "http://delta.archlinux.fr/community/os/x86_64/community.db.tar.gz"
        ),
        'parser': lambda: ArchDBParser(),
        # XXX: 'https://git.archlinux.org/svntogit/{repository}.git/tree/trunk?h=packages/{name} add support for `repository'
        'link': 'https://www.archlinux.org/packages/?sort=&q={name}',
        'tags': ['all', 'have_testdata', 'demo', 'production', 'fastfetch'],
    },
    {
        'name': 'aur',
        'desc': 'AUR',
        'family': 'arch',
        'fetcher': lambda: AURFetcher('https://aur.archlinux.org/'),
        'parser': lambda: AURParser(),
        'link': 'https://aur.archlinux.org/packages/{name}',
        'tags': ['all', 'preproduction', 'fastfetch'],
    },
    {
        'name': 'fedora_24',
        'desc': 'Fedora 24',
        'family': 'fedora',
        'fetcher': lambda: RepodataFetcher(
            "https://mirror.yandex.ru/fedora/linux/releases/24/Everything/source/tree/"
        ),
        'parser': lambda: RepodataParser(),
        'link': 'https://admin.fedoraproject.org/pkgdb/package/rpms/{name}',
        'tags': ['all', 'fedora', 'rpm', 'fastfetch'],
    },
    {
        'name': 'fedora_25',
        'desc': 'Fedora 25',
        'family': 'fedora',
        'fetcher': lambda: RepodataFetcher(
            "https://mirror.yandex.ru/fedora/linux/development/25/Everything/source/tree/"
        ),
        'parser': lambda: RepodataParser(),
        'link': 'https://admin.fedoraproject.org/pkgdb/package/rpms/{name}',
        'tags': ['all', 'fedora', 'rpm', 'fastfetch'],
    },
    {
        'name': 'fedora_rawhide',
        'desc': 'Fedora Rawhide',
        'family': 'fedora',
        'fetcher': lambda: RepodataFetcher(
            "https://mirror.yandex.ru/fedora/linux/development/rawhide/Everything/source/tree/"
        ),
        'parser': lambda: RepodataParser(),
        'link': 'https://admin.fedoraproject.org/pkgdb/package/rpms/{name}',
        'tags': ['all', 'demo', 'production', 'fedora', 'rpm', 'fastfetch'],
    },
    {
        'name': 'centos_6',
        'desc': 'CentOS 6',
        'family': 'centos',
        'fetcher': lambda: RepodataFetcher(
            "http://vault.centos.org/centos/6/os/Source/",
            "http://vault.centos.org/centos/6/updates/Source/"
        ),
        'parser': lambda: RepodataParser(),
        'link': 'http://centos-packages.com/6/package/{name}/',
        'tags': ['all', 'centos', 'rpm', 'fastfetch'],
    },
    {
        'name': 'centos_7',
        'desc': 'CentOS 7',
        'family': 'centos',
        'fetcher': lambda: RepodataFetcher(
            "http://vault.centos.org/centos/7/os/Source/",
            "http://vault.centos.org/centos/7/updates/Source/"
        ),
        'parser': lambda: RepodataParser(),
        'link': 'http://centos-packages.com/7/package/{name}/',
        'tags': ['all', 'preproduction', 'centos', 'rpm', 'fastfetch'],
    },
    {
        'name': 'mageia_6',
        'desc': 'Mageia 6',
        'family': 'mageia',
        'fetcher': lambda: RepodataFetcher(
            "https://mirrors.kernel.org/mageia/distrib/6/SRPMS/core/release/"
        ),
        'parser': lambda: RepodataParser(),
        'link': 'https://madb.mageia.org/package/show/name/{name}',
        'tags': ['all', 'mageia', 'rpm', 'fastfetch'],
    },
    {
        'name': 'mageia_cauldron',
        'desc': 'Mageia Cauldron',
        'family': 'mageia',
        'fetcher': lambda: RepodataFetcher(
            "https://mirrors.kernel.org/mageia/distrib/cauldron/SRPMS/core/release/"
        ),
        'parser': lambda: RepodataParser(),
        'link': 'https://madb.mageia.org/package/show/name/{name}',
        'tags': ['all', 'production', 'mageia', 'rpm', 'fastfetch'],
    },
    {
        'name': 'opensuse_tumbleweed',
        'desc': 'OpenSUSE Tumbleweed',
        'family': 'opensuse',
        'fetcher': lambda: RepodataFetcher(
            "http://download.opensuse.org/tumbleweed/repo/src-oss/suse/"
        ),
        'parser': lambda: RepodataParser(),
        'link': 'https://software.opensuse.org/package/{name}',
        'tags': ['all', 'demo', 'production', 'opensuse', 'rpm', 'fastfetch'],
    },
    {
        'name': 'sisyphus',
        'desc': 'ALT Sisyphus',
        'family': 'sisyphus',
        'fetcher': lambda: FileFetcher(
            "http://ftp.altlinux.org/pub/distributions/ALTLinux/Sisyphus/noarch/base/srclist.classic.xz",
            "http://ftp.altlinux.org/pub/distributions/ALTLinux/Sisyphus/x86_64/base/srclist.classic.xz",
            xz=True
        ),
        'parser': lambda: SrcListClassicParser(),
        'link': 'http://www.sisyphus.ru/en/srpm/Sisyphus/{name}',
        'tags': ['all', 'production', 'fastfetch'],
    },
    {
        'name': 'chocolatey',
        'desc': 'Chocolatey',
        'family': 'chocolatey',
        'fetcher': lambda: ChocolateyFetcher("https://chocolatey.org/api/v2/"),
        'parser': lambda: ChocolateyParser(),
        'shadow': True,
        'link': 'https://chocolatey.org/packages/{name}',
        'tags': ['all', 'production', 'fastfetch'],
    },
    {
        'name': 'yacp',
        'desc': 'YACP',
        'family': 'yacp',
        'fetcher': lambda: GitFetcher("https://github.com/fd00/yacp.git"),
        'parser': lambda: YACPGitParser(),
        'link': 'https://github.com/fd00/yacp/tree/master/{name}',
        'tags': ['all', 'preproduction', 'fastfetch'],
    },
    {
        'name': 'slackbuilds',
        'desc': 'SlackBuilds',
        'family': 'slackbuilds',
        'fetcher': lambda: GitFetcher("git://slackbuilds.org/slackbuilds"),
        'parser': lambda: SlackBuildsParser(),
        'link': 'https://slackbuilds.org/repository/14.2/{category}/{name}/',
        'tags': ['all', 'production', 'fastfetch'],
    },
    {
        'name': 'freshcode',
        'desc': 'freshcode.club',
        'family': 'freshcode',
        'fetcher': lambda: FreshcodeFetcher("http://freshcode.club/feed/xfer.json"),
        'parser': lambda: FreshcodeParser(),
        'shadow': True,
        'link': 'http://freshcode.club/projects/{name}',
        'tags': ['all', 'preproduction', 'fastfetch'],
    },
    {
        'name': 'cpan',
        'desc': 'CPAN',
        'family': 'cpan',
        'fetcher': lambda: FileFetcher("http://mirror.yandex.ru/mirrors/cpan/modules/02packages.details.txt.gz", gz=True),
        'parser': lambda: CPANPackagesParser(),
        'shadow': True,
        'link': 'http://search.cpan.org/dist/{name}',
        'tags': ['all', 'have_testdata', 'preproduction', 'fastfetch'],
    },
    {
        'name': 'pypi',
        'desc': 'PyPi',
        'family': 'pypi',
        'fetcher': lambda: FileFetcher("https://pypi.python.org/pypi/"),
        'parser': lambda: PyPiHTMLParser(),
        'shadow': True,
        'link': 'https://pypi.python.org/pypi/{name}/',
        'tags': ['all', 'preproduction', 'fastfetch'],
    },
    {
        'name': 'fdroid',
        'desc': 'F-Droid',
        'family': 'fdroid',
        'fetcher': lambda: FileFetcher("https://f-droid.org/repo/index.xml"),
        'parser': lambda: FDroidParser(),
        'shadow': True,
        'link': 'http://freshcode.club/projects/{name}',
        'tags': ['all', 'fastfetch'],
    },
]
