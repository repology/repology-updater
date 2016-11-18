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
        'name': "FreeBSD",
        'family': 'freebsd',
        'fetcher': FileFetcher("http://www.FreeBSD.org/ports/INDEX-11.bz2", bz2=True),
        'parser': FreeBSDIndexParser(),
        'link': 'http://www.freshports.org/{category}/{name}',
        'tags': ['all', 'demo', 'production', 'fastfetch'],
    },

    {
        'name': 'Debian Stable',
        'family': 'debian',
        'fetcher': FileFetcher(
            "http://ftp.debian.org/debian/dists/stable/contrib/source/Sources.gz",
            "http://ftp.debian.org/debian/dists/stable/main/source/Sources.gz",
            "http://ftp.debian.org/debian/dists/stable/non-free/source/Sources.gz",
            gz=True
        ),
        'parser': DebianSourcesParser(),
        'link': 'https://packages.debian.org/stable/{name}',
        'tags': ['all', 'debian', 'fastfetch'],
    },
    {
        'name': 'Debian Stable Backports',
        'family': 'debian',
        'fetcher': FileFetcher(
            "http://ftp.debian.org/debian/dists/stable-backports/contrib/source/Sources.gz",
            "http://ftp.debian.org/debian/dists/stable-backports/main/source/Sources.gz",
            "http://ftp.debian.org/debian/dists/stable-backports/non-free/source/Sources.gz",
            gz=True
        ),
        'parser': DebianSourcesParser(),
        'link': 'https://packages.debian.org/stable-backports/{name}',
        'tags': ['all', 'debian', 'fastfetch'],
    },
    {
        'name': 'Debian Testing',
        'family': 'debian',
        'fetcher': FileFetcher(
            "http://ftp.debian.org/debian/dists/testing/contrib/source/Sources.gz",
            "http://ftp.debian.org/debian/dists/testing/main/source/Sources.gz",
            "http://ftp.debian.org/debian/dists/testing/non-free/source/Sources.gz",
            gz=True
        ),
        'parser': DebianSourcesParser(),
        'link': 'https://packages.debian.org/testing/{name}',
        'tags': ['all', 'debian', 'fastfetch'],
    },
    {
        'name': 'Debian Unstable',
        'family': 'debian',
        'fetcher': FileFetcher(
            "http://ftp.debian.org/debian/dists/unstable/contrib/source/Sources.gz",
            "http://ftp.debian.org/debian/dists/unstable/main/source/Sources.gz",
            "http://ftp.debian.org/debian/dists/unstable/non-free/source/Sources.gz",
            gz=True
        ),
        'parser': DebianSourcesParser(),
        'link': 'https://packages.debian.org/unstable/{name}',
        'tags': ['all', 'demo', 'debian', 'production', 'fastfetch'],
    },
    {
        'name': 'Debian Experimental',
        'family': 'debian',
        'fetcher': FileFetcher(
            "http://ftp.debian.org/debian/dists/experimental/contrib/source/Sources.xz",
            "http://ftp.debian.org/debian/dists/experimental/main/source/Sources.xz",
            "http://ftp.debian.org/debian/dists/experimental/non-free/source/Sources.xz",
            xz=True
        ),
        'parser': DebianSourcesParser(),
        'link': 'https://packages.debian.org/experimental/{name}',
        'tags': ['all', 'preproduction', 'debian', 'fastfetch'],
    },

    {
        'name': 'Ubuntu Xenial',
        'family': 'debian',
        'fetcher': FileFetcher(
            "http://ftp.ubuntu.com/ubuntu/dists/xenial/main/source/Sources.gz",
            "http://ftp.ubuntu.com/ubuntu/dists/xenial/multiverse/source/Sources.gz",
            "http://ftp.ubuntu.com/ubuntu/dists/xenial/restricted/source/Sources.gz",
            "http://ftp.ubuntu.com/ubuntu/dists/xenial/universe/source/Sources.gz",
            gz=True
        ),
        'parser': DebianSourcesParser(),
        'link': 'http://packages.ubuntu.com/xenial/{name}',
        'tags': ['all', 'ubuntu', 'fastfetch'],
    },
    {
        'name': 'Ubuntu Yakkety',
        'family': 'debian',
        'fetcher': FileFetcher(
            "http://ftp.ubuntu.com/ubuntu/dists/yakkety/main/source/Sources.gz",
            "http://ftp.ubuntu.com/ubuntu/dists/yakkety/multiverse/source/Sources.gz",
            "http://ftp.ubuntu.com/ubuntu/dists/yakkety/restricted/source/Sources.gz",
            "http://ftp.ubuntu.com/ubuntu/dists/yakkety/universe/source/Sources.gz",
            gz=True
        ),
        'parser': DebianSourcesParser(),
        'link': 'http://packages.ubuntu.com/yakkety/{name}',
        'tags': ['all', 'ubuntu', 'fastfetch'],
    },
    {
        'name': 'Ubuntu Zesty',
        'family': 'debian',
        'fetcher': FileFetcher(
            "http://ftp.ubuntu.com/ubuntu/dists/zesty/main/source/Sources.gz",
            "http://ftp.ubuntu.com/ubuntu/dists/zesty/multiverse/source/Sources.gz",
            "http://ftp.ubuntu.com/ubuntu/dists/zesty/restricted/source/Sources.gz",
            "http://ftp.ubuntu.com/ubuntu/dists/zesty/universe/source/Sources.gz",
            gz=True
        ),
        'parser': DebianSourcesParser(),
        'link': 'http://packages.ubuntu.com/zesty/{name}',
        'tags': ['all', 'demo', 'production', 'ubuntu', 'fastfetch'],
    },

    {
        'name': 'Gentoo',
        'family': 'gentoo',
        'fetcher': GitFetcher("https://github.com/gentoo/gentoo.git"),
        'parser': GentooGitParser(),
        'link': 'https://packages.gentoo.org/packages/{category}/{name}',
        'tags': ['all', 'demo', 'production', 'fastfetch'],
    },
    {
        'name': 'pkgsrc',
        'family': 'pkgsrc',
        'fetcher': FileFetcher("https://ftp.netbsd.org/pub/pkgsrc/current/pkgsrc/INDEX"),
        'parser': PkgsrcIndexParser(),
        'link': 'http://cvsweb.netbsd.org/bsdweb.cgi/pkgsrc/{category}/{name}',
        'tags': ['all', 'demo', 'production', 'fastfetch'],
    },
    {
        'name': 'OpenBSD',
        'family': 'openbsd',
        'fetcher': FileFetcher("http://cvsweb.openbsd.org/cgi-bin/cvsweb/~checkout~/ports/INDEX?content-type=text/plain"),
        'parser': OpenBSDIndexParser(),
        'link': 'http://cvsweb.openbsd.org/cgi-bin/cvsweb/ports/{category}/{name}',
        'tags': ['all', 'demo', 'production', 'fastfetch'],
    },
    {
        'name': 'Arch',
        'family': 'arch',
        'fetcher': ArchDBFetcher(
            "http://delta.archlinux.fr/core/os/x86_64/core.db.tar.gz",
            "http://delta.archlinux.fr/extra/os/x86_64/extra.db.tar.gz",
            "http://delta.archlinux.fr/community/os/x86_64/community.db.tar.gz"
        ),
        'parser': ArchDBParser(),
        # XXX: 'https://git.archlinux.org/svntogit/{repository}.git/tree/trunk?h=packages/{name} add support for `repository'
        'link': 'https://www.archlinux.org/packages/?sort=&q={name}',
        'tags': ['all', 'demo', 'production', 'fastfetch'],
    },
    {
        'name': 'Fedora 24',
        'family': 'fedora',
        'fetcher': RepodataFetcher(
            "https://mirror.yandex.ru/fedora/linux/releases/24/Everything/source/tree/"
        ),
        'parser': RepodataParser(),
        'link': 'https://admin.fedoraproject.org/pkgdb/package/rpms/{name}',
        'tags': ['all', 'fedora', 'rpm', 'fastfetch'],
    },
    {
        'name': 'Fedora 25',
        'family': 'fedora',
        'fetcher': RepodataFetcher(
            "https://mirror.yandex.ru/fedora/linux/development/25/Everything/source/tree/"
        ),
        'parser': RepodataParser(),
        'link': 'https://admin.fedoraproject.org/pkgdb/package/rpms/{name}',
        'tags': ['all', 'fedora', 'rpm', 'fastfetch'],
    },
    {
        'name': 'Fedora Rawhide',
        'family': 'fedora',
        'fetcher': RepodataFetcher(
            "https://mirror.yandex.ru/fedora/linux/development/rawhide/Everything/source/tree/"
        ),
        'parser': RepodataParser(),
        'link': 'https://admin.fedoraproject.org/pkgdb/package/rpms/{name}',
        'tags': ['all', 'demo', 'production', 'fedora', 'rpm', 'fastfetch'],
    },
    {
        'name': 'CentOS 6',
        'family': 'centos',
        'fetcher': RepodataFetcher(
            "http://vault.centos.org/centos/6/os/Source/",
            "http://vault.centos.org/centos/6/updates/Source/"
        ),
        'parser': RepodataParser(),
        'link': 'http://centos-packages.com/6/package/{name}/',
        'tags': ['all', 'centos', 'rpm', 'fastfetch'],
    },
    {
        'name': 'CentOS 7',
        'family': 'centos',
        'fetcher': RepodataFetcher(
            "http://vault.centos.org/centos/7/os/Source/",
            "http://vault.centos.org/centos/7/updates/Source/"
        ),
        'parser': RepodataParser(),
        'link': 'http://centos-packages.com/7/package/{name}/',
        'tags': ['all', 'preproduction', 'centos', 'rpm', 'fastfetch'],
    },
    {
        'name': 'Mageia 6',
        'family': 'mageia',
        'fetcher': RepodataFetcher(
            "https://mirrors.kernel.org/mageia/distrib/6/SRPMS/core/release/"
        ),
        'parser': RepodataParser(),
        'link': 'https://madb.mageia.org/package/show/name/{name}',
        'tags': ['all', 'mageia', 'rpm', 'fastfetch'],
    },
    {
        'name': 'Mageia Cauldron',
        'family': 'mageia',
        'fetcher': RepodataFetcher(
            "https://mirrors.kernel.org/mageia/distrib/cauldron/SRPMS/core/release/"
        ),
        'parser': RepodataParser(),
        'link': 'https://madb.mageia.org/package/show/name/{name}',
        'tags': ['all', 'production', 'mageia', 'rpm', 'fastfetch'],
    },
    {
        'name': 'OpenSUSE Tumbleweed',
        'family': 'opensuse',
        'fetcher': RepodataFetcher(
            "http://download.opensuse.org/tumbleweed/repo/src-oss/suse/"
        ),
        'parser': RepodataParser(),
        'link': 'https://software.opensuse.org/package/{name}',
        'tags': ['all', 'demo', 'production', 'opensuse', 'rpm', 'fastfetch'],
    },
    {
        'name': 'ALT Sisyphus',
        'family': 'sisyphus',
        'fetcher': FileFetcher(
            "http://ftp.altlinux.org/pub/distributions/ALTLinux/Sisyphus/noarch/base/srclist.classic.xz",
            "http://ftp.altlinux.org/pub/distributions/ALTLinux/Sisyphus/x86_64/base/srclist.classic.xz",
            xz=True
        ),
        'parser': SrcListClassicParser(),
        'link': 'http://www.sisyphus.ru/en/srpm/Sisyphus/{name}',
        'tags': ['all', 'production', 'fastfetch'],
    },
    {
        'name': 'Chocolatey',
        'family': 'chocolatey',
        'fetcher': ChocolateyFetcher("https://chocolatey.org/api/v2/"),
        'parser': ChocolateyParser(),
        'shadow': True,
        'link': 'https://chocolatey.org/packages/{name}',
        'tags': ['all', 'production', 'fastfetch'],
    },
    {
        'name': 'SlackBuilds',
        'family': 'slackbuilds',
        'fetcher': GitFetcher("git://slackbuilds.org/slackbuilds"),
        'parser': SlackBuildsParser(),
        'link': 'https://slackbuilds.org/repository/14.2/{category}/{name}/',
        'tags': ['all', 'production', 'fastfetch'],
    },
    {
        'name': 'freshcode.club',
        'family': 'freshcode',
        'fetcher': FreshcodeFetcher("http://freshcode.club/feed/xfer.json"),
        'parser': FreshcodeParser(),
        'shadow': True,
        'link': 'http://freshcode.club/projects/{name}',
        'tags': ['all', 'preproduction', 'fastfetch'],
    },
    {
        'name': 'F-Droid',
        'family': 'fdroid',
        'fetcher': FileFetcher("https://f-droid.org/repo/index.xml"),
        'parser': FDroidParser(),
        'shadow': True,
        'link': 'http://freshcode.club/projects/{name}',
        'tags': ['all', 'fastfetch'],
    },
]
