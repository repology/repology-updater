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
import re
from argparse import ArgumentParser
from xml.sax.saxutils import escape
import shutil

from repology.package import *
from repology.nametransformer import NameTransformer
from repology.report import ReportProducer
from repology.template import Template
from repology.repositories import RepositoryManager

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
            if not maintainer in maintainers:
                maintainers[maintainer] = {
                    'sanitized_name': re.sub("[^a-zA-Z@.0-9]", "_", maintainer).lower(),
                    'num_packages': 0,
                }

            # XXX: doesn't count multiple packages with same name
            maintainers[maintainer]['num_packages'] += 1

    maintainers_path = os.path.join(path, "maintainers")
    if not os.path.isdir(maintainers_path):
        os.mkdir(maintainers_path)

    for maintainer, maintainer_data in maintainers.items():
        maint_packages = FilterPackages(packages, maintainer = maintainer)

        rp.RenderFilesPaginated(
            os.path.join(maintainers_path, maintainer_data['sanitized_name']),
            maint_packages,
            repositories,
            500,
            site_root = "../",
            subheader = "Packages maintained by " + escape(maintainer),
            subsection = "maintainers"
        )

    template.RenderToFile(
        'maintainers.html',
        os.path.join(maintainers_path, "index.html"),
        site_root = "../",
        maintainers = [
            {
                "fullname": escape(maintainer),
                "sanitizedname": maintainers[maintainer]['sanitized_name'],
                "num_packages": maintainers[maintainer]['num_packages'],
            } for maintainer in sorted(maintainers.keys())
        ],
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
    parser.add_argument('-s', '--statedir', help='directory to store repository state')
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose fetching')
    parser.add_argument('path', help='path to output file/dir')
    options = parser.parse_args()

    if options.statedir is None:
        raise RuntimeError("please set --statedir")

    repoman = RepositoryManager(options.statedir)

    print("===> Downloading package data...", file=sys.stderr)
    if not os.path.isdir(options.statedir):
        os.mkdir(options.statedir)

    repoman.Fetch(update = not options.no_update, verbose = options.verbose, tags = ['production'])

    print("===> Parsing package data...", file=sys.stderr)
    nametrans = NameTransformer(options.transform_rules)
    packages = repoman.Parse(nametrans, verbose = options.verbose, tags = ['production'])

    if options.repology_org:
        print("===> Producing repology.org website...", file=sys.stderr)
        RepologyOrg(options.path, packages, repoman.GetNames())
    elif not options.no_output:
        print("===> Producing report...", file=sys.stderr)
        packages = FilterPackages(
            packages,
            options.maintainer,
            options.category,
            int(options.number) if options.number is not None else 0,
            options.repository,
            options.no_repository
        )
        template = Template()
        rp = ReportProducer(template, "table.html")
        rp.RenderToFile(options.path, packages, repoman.GetNames())

    unmatched = nametrans.GetUnmatchedRules()
    if len(unmatched):
        print("===> Unmatched rules", file=sys.stderr)

        for rule in unmatched:
            print(rule, file=sys.stderr)

    return 0

if __name__ == '__main__':
    os.sys.exit(Main())
