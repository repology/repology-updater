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
import re
from argparse import ArgumentParser
import jinja2
from xml.sax.saxutils import escape
import shutil

from repology.processor import *
from repology.package import *
from repology.nametransformer import NameTransformer
from repology.report import ReportProducer
from repology.template import Template

REPOSITORIES = [
    { 'name': "FreeBSD", 'repotype': 'freebsd', 'processor': FreeBSDIndexProcessor("freebsd.list",
        "http://www.FreeBSD.org/ports/INDEX-11.bz2"
    ) },
    #{ 'name': 'Debian Stable', 'repotype': 'debian', 'processor': DebianSourcesProcessor("debian-stable.list",
    #    "http://ftp.debian.org/debian/dists/stable/contrib/source/Sources.gz",
    #    "http://ftp.debian.org/debian/dists/stable/main/source/Sources.gz",
    #    "http://ftp.debian.org/debian/dists/stable/non-free/source/Sources.gz"
    #) },
    #{ 'name': 'Debian Tesing', 'repotype': 'debian', 'processor': DebianSourcesProcessor("debian-testing.list",
    #    "http://ftp.debian.org/debian/dists/testing/contrib/source/Sources.gz",
    #    "http://ftp.debian.org/debian/dists/testing/main/source/Sources.gz",
    #    "http://ftp.debian.org/debian/dists/testing/non-free/source/Sources.gz"
    #) },
    # Debian unstable
    { 'name': 'Debian', 'repotype': 'debian', 'processor': DebianSourcesProcessor("debian-unstable.list",
        "http://ftp.debian.org/debian/dists/unstable/contrib/source/Sources.gz",
        "http://ftp.debian.org/debian/dists/unstable/main/source/Sources.gz",
        "http://ftp.debian.org/debian/dists/unstable/non-free/source/Sources.gz"
    ) },
    #{ 'name': 'Ubuntu Xenial', 'repotype': 'debian', 'processor': DebianSourcesProcessor("ubuntu-xenial.list",
    #    "http://ftp.ubuntu.com/ubuntu/dists/xenial/main/source/Sources.gz",
    #    "http://ftp.ubuntu.com/ubuntu/dists/xenial/multiverse/source/Sources.gz",
    #    "http://ftp.ubuntu.com/ubuntu/dists/xenial/restricted/source/Sources.gz",
    #    "http://ftp.ubuntu.com/ubuntu/dists/xenial/universe/source/Sources.gz"
    #) },
    #{ 'name': 'Ubuntu Yakkety', 'repotype': 'debian', 'processor': DebianSourcesProcessor("ubuntu-yakkety.list",
    #    "http://ftp.ubuntu.com/ubuntu/dists/yakkety/main/source/Sources.gz",
    #    "http://ftp.ubuntu.com/ubuntu/dists/yakkety/multiverse/source/Sources.gz",
    #    "http://ftp.ubuntu.com/ubuntu/dists/yakkety/restricted/source/Sources.gz",
    #    "http://ftp.ubuntu.com/ubuntu/dists/yakkety/universe/source/Sources.gz"
    #) },
    { 'name': 'Gentoo', 'repotype': 'gentoo', 'processor': GentooGitProcessor("gentoo.git",
        "https://github.com/gentoo/gentoo.git"
    ) },
    { 'name': 'NetBSD', 'repotype': 'pkgsrc', 'processor': PkgSrcReadmeAllProcessor("pkgsrc.list",
        "https://ftp.netbsd.org/pub/pkgsrc/current/pkgsrc/README-all.html"
    ) },
    { 'name': 'OpenBSD', 'repotype': 'openbsd', 'processor': OpenBSDIndexProcessor("openbsd.list",
        "http://cvsweb.openbsd.org/cgi-bin/cvsweb/~checkout~/ports/INDEX?content-type=text/plain"
    ) },
    { 'name': 'Arch', 'repotype': 'arch', 'processor': ArchDBProcessor("arch.dir",
        "http://ftp.u-tx.net/archlinux/core/os/x86_64/core.db.tar.gz",
        "http://ftp.u-tx.net/archlinux/extra/os/x86_64/extra.db.tar.gz",
        "http://ftp.u-tx.net/archlinux/community/os/x86_64/community.db.tar.gz"
    ) },
]

def MixRepositories(repositories, nametrans):
    packages = {}

    for repository in repositories:
        for package in repository['packages']:
            metaname = nametrans.TransformName(package, repository['repotype'])
            if metaname is None:
                continue
            if not metaname in packages:
                packages[metaname] = MetaPackage()
            packages[metaname].Add(repository['name'], package)

    return packages

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

def RepologyOrg(path, packages, repositories):
    if not os.path.isdir(path):
        os.mkdir(path)

    template = Template()
    rp = ReportProducer(template, "table.html")

    print("===> Main index", file=sys.stderr)
    rp.RenderFilesPaginated(
        os.path.join(path, "index"),
        packages,
        repositories,
        500,
        site_root = "",
        subheader = "Package index",
        subsection = "packages"
    )

    print("===> Per-maintainer index", file=sys.stderr)
    maintainers = {}
    for package in packages.values():
        for maintainer in package.GetMaintainers():
            maintainers[maintainer] = re.sub("[^a-zA-Z@.0-9]", "_", maintainer).lower()

    maintainers_path = os.path.join(path, "maintainers")
    if not os.path.isdir(maintainers_path):
        os.mkdir(maintainers_path)

    limit = 100
    for maintainer, sanitized_maintainer in maintainers.items():
        maint_packages = FilterPackages(packages, maintainer = maintainer)

        rp.RenderFilesPaginated(
            os.path.join(maintainers_path, sanitized_maintainer),
            maint_packages,
            repositories,
            500,
            site_root = "../",
            subheader = "Packages maintained by " + escape(maintainer),
            subsection = "maintainers"
        )

        limit -= 1
        if limit == 10000:
            break

    template.RenderToFile(
        'maintainers.html',
        os.path.join(maintainers_path, "index.html"),
        site_root = "../",
        maintainers = [ { "fullname": escape(maintainer), "sanitizedname": maintainers[maintainer] } for maintainer in sorted(maintainers.keys()) ],
        subheader = "Package maintainers",
        subsection = "maintainers"
    )

    print("===> Per-repository pages", file=sys.stderr)
    inrepo_path = os.path.join(path, "repositories")
    if not os.path.isdir(inrepo_path):
        os.mkdir(inrepo_path)

    notinrepo_path = os.path.join(path, "absent")
    if not os.path.isdir(notinrepo_path):
        os.mkdir(notinrepo_path)

    for repository in repositories:
        inrepo_packages = FilterPackages(packages, inrepo = repository)
        notinrepo_packages = FilterPackages(packages, notinrepo = repository, number = 2)

        rp.RenderFilesPaginated(
            os.path.join(inrepo_path, repository),
            inrepo_packages,
            repositories,
            500,
            site_root = "../",
            subheader = "Packages in " + repository,
            subsection = "repositories"
        )

        rp.RenderFilesPaginated(
            os.path.join(notinrepo_path, repository),
            notinrepo_packages,
            repositories,
            500,
            site_root = "../",
            subheader = "Packages absent from " + repository,
            subsection = "absent"
        )

    template.RenderToFile(
        'repositories.html',
        os.path.join(inrepo_path, "index.html"),
        site_root = "../",
        repositories = repositories,
        subheader = "Repositories",
        subsection = "repositories",
        description = '''
            For each repository, this section only lists packages it contains.
        '''
    )

    template.RenderToFile(
        'repositories.html',
        os.path.join(notinrepo_path, "index.html"),
        site_root = "../",
        repositories = repositories,
        subheader = "Repositories with absent packages",
        subsection = "absent",
        description = '''
            For each repository, this section lists packages not present in it, but present in two other repositories.
        '''
    )

    print("===> Finalizing", file=sys.stderr)
    template.RenderToFile(
        'about.html',
        os.path.join(path, "about.html"),
        site_root = "",
        subheader = "About",
        subsection = "about"
    )

    shutil.copyfile("repology.css", os.path.join(path, "repology.css"))
    shutil.copyfile(os.path.join(path, "index.0.html"), os.path.join(path, "index.html"))

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
    parser.add_argument('-o', '--repology-org', action='store_true', help='repology.org mode, static site generator')
    parser.add_argument('path', help='path to output file/dir')
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

    if options.repology_org:
        print("===> Producing repology.org website", file=sys.stderr)
        RepologyOrg(options.path, packages, [x['name'] for x in REPOSITORIES])
    elif not options.no_output:
        print("===> Producing output", file=sys.stderr)
        packages = FilterPackages(
            packages,
            options.maintainer,
            options.category,
            int(options.number) if options.number is not None else 0,
            options.repository,
            options.no_repository
        )
        rp = ReportProducer()
        rp.RenderFile('table.html', options.path, packages, [x['name'] for x in REPOSITORIES])

    unmatched = nametrans.GetUnmatchedRules()
    if len(unmatched):
        print("===> Unmatched rules", file=sys.stderr)

        for rule in unmatched:
            print(rule, file=sys.stderr)

    return 0

if __name__ == '__main__':
    os.sys.exit(Main())
