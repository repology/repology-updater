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
        'name': 'Fedora',
        'family': 'fedora',
        'fetcher': FedoraFetcher(
            "https://admin.fedoraproject.org/pkgdb/api/",
            "http://pkgs.fedoraproject.org/cgit/rpms/"
        ),
        'parser': SpecParser(),
        'incomplete': True,
        'link': 'http://pkgs.fedoraproject.org/cgit/rpms/{name}.git/tree/',
        'tags': ['all', 'preproduction', 'slowfetch'],
    },
    {
        'name': 'OpenSUSE Tumbleweed',
        'family': 'opensuse',
        'fetcher': OpenSUSERepodataFetcher(
            "http://download.opensuse.org/tumbleweed/repo/src-oss/suse/"
        ),
        'parser': OpenSUSERepodataParser(),
        'link': 'https://software.opensuse.org/package/{name}',
        'tags': ['all', 'production', 'opensuse', 'fastfetch'],
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
]
