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

import os
import sys
import pickle
import fcntl

from repology.fetcher import *
from repology.parser import *

from repology.package import *
from repology.logger import *

REPOSITORIES = [
    {
        'name': "FreeBSD",
        'repotype': 'freebsd',
        'fetcher': FileFetcher("http://www.FreeBSD.org/ports/INDEX-11.bz2", bz2=True),
        'parser': FreeBSDIndexParser(),
        'link': 'http://www.freshports.org/{category}/{name}',
        'tags': ['all', 'demo', 'production', 'fastfetch'],
    },

    {
        'name': 'Debian Stable',
        'repotype': 'debian',
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
        'repotype': 'debian',
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
        'repotype': 'debian',
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
        'repotype': 'debian',
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
        'repotype': 'debian',
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
        'repotype': 'gentoo',
        'fetcher': GitFetcher("https://github.com/gentoo/gentoo.git"),
        'parser': GentooGitParser(),
        'link': 'https://packages.gentoo.org/packages/{category}/{name}',
        'tags': ['all', 'demo', 'production', 'fastfetch'],
    },
    {
        'name': 'pkgsrc',
        'repotype': 'pkgsrc',
        'fetcher': FileFetcher("https://ftp.netbsd.org/pub/pkgsrc/current/pkgsrc/INDEX"),
        'parser': PkgsrcIndexParser(),
        'link': 'http://cvsweb.netbsd.org/bsdweb.cgi/pkgsrc/{category}/{name}',
        'tags': ['all', 'demo', 'production', 'fastfetch'],
    },
    {
        'name': 'OpenBSD',
        'repotype': 'openbsd',
        'fetcher': FileFetcher("http://cvsweb.openbsd.org/cgi-bin/cvsweb/~checkout~/ports/INDEX?content-type=text/plain"),
        'parser': OpenBSDIndexParser(),
        'link': 'http://cvsweb.openbsd.org/cgi-bin/cvsweb/ports/{category}/{name}',
        'tags': ['all', 'demo', 'production', 'fastfetch'],
    },
    {
        'name': 'Arch',
        'repotype': 'arch',
        'fetcher': ArchDBFetcher(
            "http://delta.archlinux.fr/core/os/x86_64/core.db.tar.gz",
            "http://delta.archlinux.fr/extra/os/x86_64/extra.db.tar.gz",
            "http://delta.archlinux.fr/community/os/x86_64/community.db.tar.gz"
        ),
        'parser': ArchDBParser(),
        'link': 'https://git.archlinux.org/svntogit/{repository}.git/tree/trunk?h=packages/{name}',
        'tags': ['all', 'demo', 'production', 'fastfetch'],
    },
    {
        'name': 'Fedora',
        'repotype': 'fedora',
        'fetcher': FedoraFetcher(
            "https://admin.fedoraproject.org/pkgdb/api/",
            "http://pkgs.fedoraproject.org/cgit/rpms/"
        ),
        'parser': SpecParser(),
        'incomplete': True,
        'link': 'http://pkgs.fedoraproject.org/cgit/rpms/{name}.git/tree/',
        'tags': ['all', 'preproduction', 'slowfetch'],
    },
    # These parse binary package lists, and produce results not suitable for comparison
    # with other repos. For instance, for each `libfoo' other repos have these will
    # have `libfoo-devel', `libfooN` and `libfooN-32bit`. Merging these with rules
    # is incorrect and errorprone, so switching this to getting and parsing a bunch
    # of .specs is needed
    {
        'name': 'OpenSUSE Tumbleweed',
        'repotype': 'opensuse',
        'fetcher': FileFetcher(
            "http://download.opensuse.org/tumbleweed/repo/oss/suse/noarch/",
            "http://download.opensuse.org/tumbleweed/repo/oss/suse/x86_64/"
        ),
        'parser': OpenSUSEPackageListParser(),
        'shadow': True,
        'incomplete': True,
        'tags': ['all', 'preproduction', 'opensuse', 'fastfetch'],
    },
    {
        'name': 'OpenSUSE Leap',
        'repotype': 'opensuse',
        'fetcher': FileFetcher(
            "http://download.opensuse.org/distribution/leap/42.1/repo/oss/suse/noarch/",
            "http://download.opensuse.org/distribution/leap/42.1/repo/oss/suse/x86_64/"
        ),
        'parser': OpenSUSEPackageListParser(),
        'shadow': True,
        'incomplete': True,
        'tags': ['all', 'opensuse', 'fastfetch'],
    },
    {
        'name': 'Sisyphus',
        'repotype': 'sisyphus',
        'fetcher': FileFetcher(
            "http://ftp.altlinux.org/pub/distributions/ALTLinux/Sisyphus/noarch/base/srclist.classic.xz",
            "http://ftp.altlinux.org/pub/distributions/ALTLinux/Sisyphus/x86_64/base/srclist.classic.xz",
            xz=True
        ),
        'parser': SrcListClassicParser(),
        'tags': ['all', 'preproduction', 'fastfetch'],
    },
    {
        'name': 'Chocolatey',
        'repotype': 'chocolatey',
        'fetcher': ChocolateyFetcher("https://chocolatey.org/api/v2/"),
        'parser': ChocolateyParser(),
        'shadow': True,
        'link': 'https://chocolatey.org/packages/{name}',
        'tags': ['all', 'preproduction', 'slowfetch'],
    },
]


class RepositoryManager:
    def __init__(self, statedir, enable_shadow=True, logger=NoopLogger()):
        self.statedir = statedir
        self.enable_shadow = enable_shadow
        self.logger = logger

    def GetStatePath(self, repository):
        return os.path.join(self.statedir, repository['name'] + ".state")

    def GetSerializedPath(self, repository, tmp=False):
        tmpext = ".tmp" if tmp else ""
        return os.path.join(self.statedir, repository['name'] + ".packages" + tmpext)

    def ForEach(self, processor, tags=None, repositories=None):
        for repository in REPOSITORIES:
            if repositories and not repository['name'] in repositories:
                continue

            skip = False
            if tags:
                for tagset in tags:
                    skip = True
                    for tag in tagset if type(tagset) is list else [tagset]:
                        if tag in repository['tags']:
                            skip = False
                            break
                    if skip:
                        break

            if not skip:
                processor(repository)

    def GetNames(self, tags=None, repositories=None):
        names = []

        def AppendName(repository):
            names.append(repository['name'])

        self.ForEach(AppendName, tags=tags, repositories=repositories)

        return names

    def GetMetadata(self):
        return {repository['name']: {
            'incomplete': repository['incomplete'] if 'incomplete' in repository else False,
        } for repository in REPOSITORIES}

    def Fetch(self, update=True, tags=None, repositories=None):
        def Fetcher(repository):
            logger = self.logger.GetPrefixed(repository['name'] + ": ")
            logger.Log("fetching started")
            repository['fetcher'].Fetch(self.GetStatePath(repository), update=update, logger=logger)
            logger.Log("fetching complete")

        if not os.path.isdir(self.statedir):
            os.mkdir(self.statedir)

        self.ForEach(Fetcher, tags, repositories)

    def Mix(self, packages_by_repo, name_transformer):
        packages = {}

        for repository in REPOSITORIES:
            reponame = repository['name']
            if reponame not in packages_by_repo:
                continue

            for package in packages_by_repo[reponame]:
                metaname = name_transformer.TransformName(package, repository['repotype'])

                if metaname is None:
                    continue
                if metaname not in packages:
                    packages[metaname] = MetaPackage(metaname)
                packages[metaname].Add(reponame, package)

        for package in packages.values():
            package.FillVersionData()

        shadows = set()

        if self.enable_shadow:
            for repository in REPOSITORIES:
                if 'shadow' in repository and repository['shadow']:
                    shadows.add(repository['name'])

        def CheckShadows(package):
            for repo in package.versions.keys():
                if repo not in shadows:
                    return True

            return False

        return [packages[name] for name in sorted(packages.keys()) if CheckShadows(packages[name])]

    def Parse(self, name_transformer, tags=None, repositories=None):
        packages_by_repo = {}

        def Parser(repository):
            logger = self.logger.GetPrefixed(repository['name'] + ": ")
            logger.Log("parsing started")
            repo_packages = repository['parser'].Parse(self.GetStatePath(repository))
            packages_by_repo[repository['name']] = repo_packages
            logger.Log("parsing complete, {} packages".format(len(repo_packages)))

        self.ForEach(Parser, tags, repositories)

        self.logger.Log("merging started")
        packages = self.Mix(packages_by_repo, name_transformer)
        self.logger.Log("merging complete, {} metapackages".format(len(packages)))
        return packages

    def ParseAndSerialize(self, tags=None, repositories=None):
        def ParserSerializer(repository):
            logger = self.logger.GetPrefixed(repository['name'] + ": ")
            logger.Log("parsing + saving started")
            repo_packages = repository['parser'].Parse(self.GetStatePath(repository))
            pickle.dump(
                repo_packages,
                open(self.GetSerializedPath(repository, tmp=True), "wb")
            )
            os.rename(self.GetSerializedPath(repository, tmp=True), self.GetSerializedPath(repository))
            logger.Log("parsing + saving complete, {} packages".format(len(repo_packages)))

        self.ForEach(ParserSerializer, tags, repositories)

    def Deserialize(self, name_transformer, tags=None, repositories=None):
        packages_by_repo = {}

        def Deserializer(repository):
            logger = self.logger.GetPrefixed(repository['name'] + ": ")
            logger.Log("loading started")
            repo_packages = pickle.load(open(self.GetSerializedPath(repository), "rb"))
            packages_by_repo[repository['name']] = repo_packages
            logger.Log("loading complete, {} packages".format(len(repo_packages)))

        self.ForEach(Deserializer, tags, repositories)

        self.logger.Log("merging started")
        packages = self.Mix(packages_by_repo, name_transformer)
        self.logger.Log("merging complete, {} metapackages".format(len(packages)))
        return packages
