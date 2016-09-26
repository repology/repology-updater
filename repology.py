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
import time
from argparse import ArgumentParser
import jinja2

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
    { 'name': 'NetBSD', 'processor': PkgSrcReadmeAllProcessor("pkgsrc.list",
        "https://ftp.netbsd.org/pub/pkgsrc/current/pkgsrc/README-all.html"
    ) },
    { 'name': 'OpenBSD', 'processor': OpenBSDIndexProcessor("openbsd.list",
        "http://cvsweb.openbsd.org/cgi-bin/cvsweb/~checkout~/ports/INDEX?content-type=text/plain"
    ) },
    { 'name': 'Arch', 'processor': ArchDBProcessor("arch.dir",
        "http://ftp.u-tx.net/archlinux/core/os/x86_64/core.db.tar.gz",
        "http://ftp.u-tx.net/archlinux/extra/os/x86_64/extra.db.tar.gz",
        "http://ftp.u-tx.net/archlinux/community/os/x86_64/community.db.tar.gz"
    ) },
]

def MixRepositories(repositories, nametrans):
    packages = {}

    for repository in repositories:
        for package in repository['packages']:
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

def FilterPackages(packages, maintainer = None, category = None, number = 0, inrepo = None, notinrepo = None):
    filtered_packages = {}

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

        filtered_packages[pkgname] = metapackage

    return filtered_packages

def PrintPackageTable(packages, reponames):
    env = jinja2.Environment(loader = jinja2.PackageLoader('repology', 'templates'),
        lstrip_blocks = True,
        trim_blocks = True
    )
    template = env.get_template('table.html')

    template_args = {
        'reponames': reponames,
        'repositories': {},
        'packages': [],
        'gentime': time.strftime("%Y-%m-%d %H:%M UTC", time.gmtime())
    }

    for reponame in reponames:
        template_args['repositories'][reponame] = {
            'statistics': {
                'total': 0,
                'lonely': 0,
                'good': 0,
                'multi': 0,
                'bad': 0,
                'ignore': 0
            }
        }

    for pkgname in sorted(packages.keys()):
        metapackage = packages[pkgname]

        bestversion, _, _ = metapackage.GetMaxVersion()

        template_package = {
            'name': pkgname,
            'byrepo': {}
        }

        for reponame in reponames:
            # packages for this repository
            repopackages = metapackage.Get(reponame)
            if repopackages is None:
                continue

            # determine versions
            repominversion, repomaxversion = metapackage.GetVersionRangeForRepo(reponame)

            versionclass = 'bad'
            if metapackage.GetNumRepos() == 1:
                versionclass = 'lonely'
            elif bestversion is None:
                versionclass = 'good'
            elif VersionCompare(repomaxversion, bestversion) > 0: # due to ignore
                versionclass = 'ignore'
            elif VersionCompare(repomaxversion, bestversion) >= 0:
                if VersionCompare(repominversion, bestversion) == 0:
                    versionclass = 'good'
                else:
                    versionclass = 'multi'

            template_package['byrepo'][reponame] = {
                'version': repomaxversion,
                'class': versionclass,
                'numpackages': len(repopackages)
            }

            template_args['repositories'][reponame]['statistics']['total'] += 1
            template_args['repositories'][reponame]['statistics'][versionclass] += 1

        template_args['packages'].append(template_package)

    print(template.render(template_args))

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
        print("===> Downloading %s" % repository['name'], file=sys.stderr)
        if repository['processor'].IsUpToDate():
            print("Up to date", file=sys.stderr)
        else:
            repository['processor'].Download(not options.no_update)

    nametrans = NameTransformer(options.transform_rules)

    for repository in REPOSITORIES:
        print("===> Parsing %s" % repository['name'], file=sys.stderr)
        repository['packages'] = repository['processor'].Parse()

    print("===> Processing", file=sys.stderr)
    packages = MixRepositories(REPOSITORIES, nametrans)

    if not options.no_output:
        print("===> Producing output", file=sys.stderr)
        packages = FilterPackages(
            packages,
            options.maintainer,
            options.category,
            int(options.number) if options.number is not None else 0,
            options.repository,
            options.no_repository
        )
        PrintPackageTable(
            packages,
            [x['name'] for x in REPOSITORIES]
        )

    unmatched = nametrans.GetUnmatchedRules()
    if len(unmatched):
        print("===> Unmatched rules", file=sys.stderr)

        for rule in unmatched:
            print(rule, file=sys.stderr)

    return 0

if __name__ == '__main__':
    os.sys.exit(Main())
