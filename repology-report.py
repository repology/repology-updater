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

def Main():
    parser = ArgumentParser()
    parser.add_argument('-s', '--statedir', help='path to directory with repository state')
    parser.add_argument('-U', '--rules', default='rules.yaml', help='path to name transformation rules yaml')
    parser.add_argument('-v', '--verbose', action='store_true', help='verbose output')

    parser.add_argument('-t', '--tag', action='append', help='only process repositories with this tag')
    parser.add_argument('-r', '--repository', action='append', help='only process repositories with this name')

    parser.add_argument('-m', '--maintainer', help='filter by maintainer')
    parser.add_argument('-c', '--category', help='filter by category')
    parser.add_argument('-n', '--number', help='filter by number of repos')
    parser.add_argument('-i', '--in-repository', help='filter by presence in repository')
    parser.add_argument('-x', '--not-in-repository', help='filter by absence in repository')
    parser.add_argument('-O', '--outdated-in-repository', help='filter by outdatedness in repository')

    parser.add_argument('-o', '--output', help='path to output file')
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

    packages = FilterPackages(
        packages,
        options.maintainer,
        options.category,
        int(options.number) if options.number is not None else 0,
        options.in_repository,
        options.not_in_repository,
        options.outdated_in_repository
    )

    template = Template()
    rp = ReportProducer(template, "table.html")
    rp.RenderToFile(options.output, packages, repoman.GetNames(tags = options.tag, repositories = options.repository))

    unmatched = nametrans.GetUnmatchedRules()
    if len(unmatched):
        print("WARNING: Unmatched rules detected:", file=sys.stderr)

        for rule in unmatched:
            print(rule, file=sys.stderr)

    return 0

if __name__ == '__main__':
    os.sys.exit(Main())
