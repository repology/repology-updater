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

def FilterPackages(metapackages, maintainer = None, category = None, number = 0, inrepo = None, notinrepo = None, outdatedinrepo = None):
    filtered = []

    for metapackage in metapackages:
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

        if outdatedinrepo is not None and not metapackage.IsOutdatedInRepository(outdatedinrepo):
            continue

        filtered.append(metapackage)

    return filtered

def RepologyOrg(path, metapackages, repositories, repometadata):
    if not os.path.isdir(path):
        os.mkdir(path)

    template = Template()
    rp = ReportProducer(template, "table.html")

    print("===> Basic stuff", file=sys.stderr)
    template.RenderToFile(
        'about.html',
        os.path.join(path, "about.html"),
        site_root = "",
        subheader = "About",
        subsection = "about"
    )

    shutil.copyfile("repology.css", os.path.join(path, "repology.css"))

    print("===> Main index", file=sys.stderr)
    rp.RenderFilesPaginated(
        os.path.join(path, "index"),
        metapackages,
        repositories,
        500,
        repositories = repometadata,
        site_root = "",
        subheader = "Package index",
        subsection = "packages"
    )

    shutil.copyfile(os.path.join(path, "index.0.html"), os.path.join(path, "index.html"))

    print("===> Per-repository pages", file=sys.stderr)
    inrepo_path = os.path.join(path, "repositories")
    if not os.path.isdir(inrepo_path):
        os.mkdir(inrepo_path)

    notinrepo_path = os.path.join(path, "absent")
    if not os.path.isdir(notinrepo_path):
        os.mkdir(notinrepo_path)

    outdatedinrepo_path = os.path.join(path, "outdated")
    if not os.path.isdir(outdatedinrepo_path):
        os.mkdir(outdatedinrepo_path)

    for repository in repositories:
        inrepo_packages = FilterPackages(metapackages, inrepo = repository)
        notinrepo_packages = FilterPackages(metapackages, notinrepo = repository, number = 2)
        outdatedinrepo_packages = FilterPackages(metapackages, outdatedinrepo = repository)

        rp.RenderFilesPaginated(
            os.path.join(inrepo_path, repository),
            inrepo_packages,
            repositories,
            500,
            repositories = repometadata,
            site_root = "../",
            subheader = "Packages in " + repository,
            subsection = "repositories"
        )

        rp.RenderFilesPaginated(
            os.path.join(notinrepo_path, repository),
            notinrepo_packages,
            repositories,
            500,
            repositories = repometadata,
            site_root = "../",
            subheader = "Packages absent from " + repository,
            subsection = "absent"
        )

        rp.RenderFilesPaginated(
            os.path.join(outdatedinrepo_path, repository),
            outdatedinrepo_packages,
            repositories,
            500,
            repositories = repometadata,
            site_root = "../",
            subheader = "Packages outdated in " + repository,
            subsection = "outdated"
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

    template.RenderToFile(
        'repositories.html',
        os.path.join(outdatedinrepo_path, "index.html"),
        site_root = "../",
        repositories = repositories,
        subheader = "Repositories with outdated packages",
        subsection = "outdated",
    )

    print("===> Per-maintainer index", file=sys.stderr)
    maintainers = {}
    for metapackage in metapackages:
        for maintainer in metapackage.GetMaintainers():
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
        maint_packages = FilterPackages(metapackages, maintainer = maintainer)

        rp.RenderFilesPaginated(
            os.path.join(maintainers_path, maintainer_data['sanitized_name']),
            maint_packages,
            repositories,
            500,
            repositories = repometadata,
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

def Main():
    parser = ArgumentParser()
    parser.add_argument('-s', '--statedir', help='path to directory with repository state')
    parser.add_argument('-U', '--rules', default='rules.yaml', help='path to name transformation rules yaml')
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose output')

    parser.add_argument('-t', '--tag', action='append', help='only process repositories with this tag')
    parser.add_argument('-r', '--repository', action='append', help='only process repositories with this name')

    parser.add_argument('-o', '--output', help='path to output directory')
    options = parser.parse_args()

    if not options.statedir:
        raise RuntimeError("please set --statedir")
    if not options.tag and not options.repository:
        raise RuntimeError("please set --tag or --repository")

    nametrans = NameTransformer(options.rules)
    repoman = RepositoryManager(options.statedir)
    packages = repoman.Deserialize(
        nametrans,
        verbose = options.verbose,
        tags = options.tag,
        repositories = options.repository
    )

    RepologyOrg(options.output, packages, repoman.GetNames(tags = options.tag, repositories = options.repository), repoman.GetMetadata())

    unmatched = nametrans.GetUnmatchedRules()
    if len(unmatched):
        print("WARNING: Unmatched rules detected:", file=sys.stderr)

        for rule in unmatched:
            print(rule, file=sys.stderr)

    return 0

if __name__ == '__main__':
    os.sys.exit(Main())
