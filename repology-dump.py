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
from repology.report import ReportProducer
from repology.template import Template
from repology.repoman import RepositoryManager
from repology.logger import *
from repology.filters import *


def Main():
    parser = ArgumentParser()
    parser.add_argument('-s', '--statedir', default='_state', help='path to directory with repository state')
    parser.add_argument('-l', '--logfile', help='path to log file')

    parser.add_argument('-r', '--repository', action='append', help='specify repository names or tags to process')
    parser.add_argument('-S', '--no-shadow', action='store_true', help='treat shadow repositories as normal')

    parser.add_argument('-m', '--maintainer', help='filter by maintainer')
    parser.add_argument('-c', '--category', help='filter by category')
    parser.add_argument('-n', '--less-repos', help='filter by number of repos')
    parser.add_argument('-N', '--more-repos', help='filter by number of repos')
    parser.add_argument('-i', '--in-repository', help='filter by presence in repository')
    parser.add_argument('-x', '--not-in-repository', help='filter by absence in repository')
    parser.add_argument('-O', '--outdated-in-repository', help='filter by outdatedness in repository')

    parser.add_argument('-d', '--dump', help='dump mode (packages|summaries)')
    options = parser.parse_args()

    if not options.repository:
        options.repository = ["all"]

    logger = StderrLogger()
    if options.logfile:
        logger = FileLogger(options.logfile)

    # Set up filters
    filters = []
    if options.maintainer:
        filters.append(MaintainerFilter(options.maintainer))
    if options.category:
        filters.append(CategoryFilter(options.maintainer))
    if options.more_repos is not None or options.less_repos is not None:
        filters.append(FamilyCountFilter(more=options.more_repos, less=options.less_repos))
    if options.in_repository:
        filters.append(InRepoFilter(options.in_repository))
    if options.not_in_repository:
        filters.append(NotInRepoFilter(options.not_in_repository))
    if options.outdated_in_repository:
        filters.append(OutdatedInRepoFilter(options.not_in_repository))

    # Process package data
    repoman = RepositoryManager(options.statedir, enable_shadow=not options.no_shadow)
    logger.Log("loading packages started")
    packages = repoman.DeserializeMulti(reponames=options.repository, logger=logger)
    logger.Log("loading packages complete")
    logger.Log("merging packages started")
    metapackages = MergeMetapackages(packages)
    logger.Log("merging packages complete")
    logger.Log("package versions processing started")
    FillMetapackagesVersionInfos(metapackages)
    logger.Log("package versions processing complete")
    if filters:
        logger.Log("filtering started")
        metapackages = FilterMetapackages(metapackages, *filters)
        logger.Log("filtering complete")

    logger.Log("summary production started")
    summaries = ProduceMetapackagesSummaries(metapackages)
    logger.Log("summary production complete")

    logger.Log("dumping started")
    # Produce output
    for metaname in sorted(summaries.keys()):
        print("{}".format(metaname))
        if options.dump == 'packages':
            for package in metapackages[metaname]:
                print("  {}: {}-{} ({})".format(
                    package.repo,
                    package.name,
                    package.version,
                    PackageVersionClass.ToChar(package.versionclass),
                ))
        if options.dump == 'summaries':
            for reponame in repoman.GetNames(options.repository):
                if reponame in summaries[metaname]:
                    print("  {}: {} ({}) *{}".format(
                        reponame,
                        summaries[metaname][reponame]['version'],
                        RepositoryVersionClass.ToChar(summaries[metaname][reponame]['versionclass']),
                        summaries[metaname][reponame]['numpackages'],
                    ))

    logger.Log("dumping complete")

    return 0

if __name__ == '__main__':
    os.sys.exit(Main())
