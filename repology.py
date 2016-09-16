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
from argparse import ArgumentParser

from repology.processor import *
from repology.package import *
from repology.nametransformer import NameTransformer

REPOSITORIES = [
    { 'name': "FreeBSD", 'processor': FreeBSDIndexProcessor("freebsd.list",
        "http://www.FreeBSD.org/ports/INDEX-11.bz2"
    ) },
    #{ 'name': 'Debian Stable', 'processor': DebianSourcesProcessor("debian-stable.list",
    #    "http://ftp.debian.org/debian/dists/stable/contrib/source/Sources.gz",
    #    "http://ftp.debian.org/debian/dists/stable/main/source/Sources.gz",
    #    "http://ftp.debian.org/debian/dists/stable/non-free/source/Sources.gz"
    #) },
    #{ 'name': 'Debian Tesing', 'processor': DebianSourcesProcessor("debian-testing.list",
    #    "http://ftp.debian.org/debian/dists/testing/contrib/source/Sources.gz",
    #    "http://ftp.debian.org/debian/dists/testing/main/source/Sources.gz",
    #    "http://ftp.debian.org/debian/dists/testing/non-free/source/Sources.gz"
    #) },
    # Debian unstable
    { 'name': 'Debian', 'processor': DebianSourcesProcessor("debian-unstable.list",
        "http://ftp.debian.org/debian/dists/unstable/contrib/source/Sources.gz",
        "http://ftp.debian.org/debian/dists/unstable/main/source/Sources.gz",
        "http://ftp.debian.org/debian/dists/unstable/non-free/source/Sources.gz"
    ) },
    #{ 'name': 'Ubuntu Xenial', 'processor': DebianSourcesProcessor("ubuntu-xenial.list",
    #    "http://ftp.ubuntu.com/ubuntu/dists/xenial/main/source/Sources.gz",
    #    "http://ftp.ubuntu.com/ubuntu/dists/xenial/multiverse/source/Sources.gz",
    #    "http://ftp.ubuntu.com/ubuntu/dists/xenial/restricted/source/Sources.gz",
    #    "http://ftp.ubuntu.com/ubuntu/dists/xenial/universe/source/Sources.gz"
    #) },
    #{ 'name': 'Ubuntu Yakkety', 'processor': DebianSourcesProcessor("ubuntu-yakkety.list",
    #    "http://ftp.ubuntu.com/ubuntu/dists/yakkety/main/source/Sources.gz",
    #    "http://ftp.ubuntu.com/ubuntu/dists/yakkety/multiverse/source/Sources.gz",
    #    "http://ftp.ubuntu.com/ubuntu/dists/yakkety/restricted/source/Sources.gz",
    #    "http://ftp.ubuntu.com/ubuntu/dists/yakkety/universe/source/Sources.gz"
    #) },
    { 'name': 'Gentoo', 'processor': GentooGitProcessor("gentoo.git",
        "https://github.com/gentoo/gentoo.git"
    ) },
    { 'name': 'NetBSD', 'processor': PkgSrcPackagesSHA512Processor("pkgsrc.list",
        "https://ftp.netbsd.org/pub/pkgsrc/packages/NetBSD/amd64/7.0_current/SHA512.bz2"
    ) },
    { 'name': 'OpenBSD', 'processor': OpenBSDIndexProcessor("openbsd.git",
        "http://cvsweb.openbsd.org/cgi-bin/cvsweb/~checkout~/ports/INDEX?content-type=text/plain"
    ) },
]

def MixRepositories(repositories, nametrans):
    packages = {}

    for repository in repositories:
        for package in repository['processor'].Parse():
            metaname = nametrans.TransformName(package, repository['processor'].GetRepoType())
            if metaname is None:
                continue
            if not metaname in packages:
                packages[metaname] = MetaPackage()
            packages[metaname].Add(repository['name'], package)

    return packages

def Trim(str, maxlength):
    if len(str) <= maxlength:
        return str

    return "<span title=\"%s\">%s...</span>" % (str, str[0:maxlength])

def PrintPackageTable(packages, repositories, maintainer = None, category = None, number = 0, inrepo = None, notinrepo = None):
    statistics = {}

    print("<html>")
    print("<head>");
    print("<html><head><title>Repology</title>")
    print("<link rel=\"stylesheet\" media=\"screen\" href=\"repology.css\">")
    print("</head>")
    print("<body>")
    print("<table>")
    print("<tr><th>Package</th>")
    for repository in repositories:
        print("<th>%s</th>" % repository['name'])
        statistics[repository['name']] = { 'total': 0, 'lonely': 0, 'good': 0, 'multi': 0, 'bad': 0 }
    print("</tr>")

    for pkgname in sorted(packages.keys()):
        metapackage = packages[pkgname]

        if maintainer is not None and not metapackage.HasMaintainer(maintainer):
            continue

        if category is not None and not metapackage.HasCategoryLike(category):
            continue

        if number > 0 and metapackage.GetNumRepos() < number:
            continue

        if inrepo is not None and not metapackage.HasRepository(inrepo):
            continue

        if notinrepo is not None and metapackage.HasRepository(notinrepo):
            continue

        print("<tr>")
        print("<td>%s</td>" % (Trim(pkgname, 50)))

        bestversion, _, _ = metapackage.GetMaxVersion()

        for repo in repositories:
            reponame = repo['name']

            # packages for this repository
            repopackages = metapackage.Get(reponame)
            if repopackages is None:
                print("<td>-</td>")
                continue

            # determine versions
            repominversion, repomaxversion = metapackage.GetVersionRangeForRepo(reponame)

            versionclass = 'bad'
            if metapackage.GetNumRepos() == 1:
                versionclass = 'lonely'
            elif VersionCompare(repomaxversion, bestversion) == 0:
                if VersionCompare(repominversion, bestversion) == 0:
                    versionclass = 'good'
                else:
                    versionclass = 'multi'

            print("<td><span class=\"version %s\">%s</span>" % (versionclass, Trim(repomaxversion, 20)))
            if (len(repopackages) > 1):
                print(" (%d)" % len(repopackages));
            print("</td>");

            statistics[reponame]['total'] += 1
            statistics[reponame][versionclass] += 1

        print("</tr>")

    print("<tr>")
    print("<th>%d</th>" % len(packages))
    for repo in repositories:
        reponame = repo['name']
        print("<th>%d<br><span class=\"version lonely\">%d</span><br><span class=\"version good\">%d</span><br><span class=\"version multi\">%d</span><br><span class=\"version bad\">%d (%.2f%%)</span></th>" % (
                statistics[reponame]['total'],
                statistics[reponame]['lonely'],
                statistics[reponame]['good'],
                statistics[reponame]['multi'],
                statistics[reponame]['bad'],
                statistics[reponame]['bad'] / (1 if statistics[reponame]['total'] == 0 else statistics[reponame]['total']) * 100.0
            ))
    print("</tr>")

    print("</table>")
    print("</body>")
    print("</html>")

def Main():
    parser = ArgumentParser()
    parser.add_argument('-U', '--no-update', action='store_true', help='don\'t update databases')
    parser.add_argument('-t', '--transform-rules', default='rules.yaml', help='path to name transformation rules yaml')
    parser.add_argument('-m', '--maintainer', help='filter by maintainer')
    parser.add_argument('-c', '--category', help='filter by category')
    parser.add_argument('-n', '--number', help='filter by number of repos')
    parser.add_argument('-r', '--repository', help='filter by presence in repository')
    parser.add_argument('-R', '--no-repository', help='filter by absence in repository')
    parser.add_argument('-x', '--no-output', action='store_true', help='do not output anything')
    options = parser.parse_args()

    for repository in REPOSITORIES:
        print("===> Downloading for %s" % repository['name'], file=sys.stderr)
        if repository['processor'].IsUpToDate():
            print("Up to date", file=sys.stderr)
        else:
            repository['processor'].Download(not options.no_update)

    nametrans = NameTransformer(options.transform_rules)

    print("===> Processing", file=sys.stderr)
    packages = MixRepositories(REPOSITORIES, nametrans)

    if not options.no_output:
        print("===> Producing output", file=sys.stderr)
        PrintPackageTable(
            packages,
            REPOSITORIES,
            options.maintainer,
            options.category,
            int(options.number) if options.number is not None else 0,
            options.repository,
            options.no_repository
        )

    return 0

if __name__ == '__main__':
    os.sys.exit(Main())
