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
    parser.add_argument('-l', '--logfile', help='path to log file (log to stderr by default)')
    parser.add_argument('-m', '--mode', choices=['batch', 'stream'], default='stream', help='processing mode')

    filters_grp = parser.add_argument_group('Filters')
    filters_grp.add_argument('-S', '--no-shadow', action='store_true', help='treat shadow repositories as normal')
    filters_grp.add_argument(      '--maintainer', help='filter by maintainer')
    filters_grp.add_argument(      '--category', help='filter by category')
    filters_grp.add_argument(      '--less-repos', help='filter by number of repos')
    filters_grp.add_argument(      '--more-repos', help='filter by number of repos')
    filters_grp.add_argument(      '--in-repository', help='filter by presence in repository')
    filters_grp.add_argument(      '--not-in-repository', help='filter by absence in repository')
    filters_grp.add_argument(      '--outdated-in-repository', help='filter by outdatedness in repository')

    parser.add_argument('-d', '--dump', choices=['packages', 'summaries'], default='packages', help='dump mode')

    parser.add_argument('reponames', metavar='repo|tag', nargs='+', help='repository or tag name to process')
    options = parser.parse_args()

    if not options.reponames:
        options.reponames = ["all"]

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
    if not options.no_shadow:
        filters.append(ShadowFilter())

    repoman = RepositoryManager(options.statedir)

    def PackageProcessor(packages):
        name = packages[0].effname
        FillVersionInfos(packages)

        if not CheckFilters(packages, *filters):
            return

        if options.dump == 'packages':
            print(packages[0].effname)
            for package in packages:
                print("  {}: {}-{} ({})".format(
                    package.repo,
                    package.name,
                    package.version,
                    PackageVersionClass.ToChar(package.versionclass),
                ))
        if options.dump == 'summaries':
            print(packages[0].effname)
            summary = ProduceRepositorySummary(packages)
            for reponame in repoman.GetNames(options.reponames):
                if reponame in summary:
                    print("  {}: {} ({}) *{}".format(
                        reponame,
                        summary[reponame]['version'],
                        RepositoryVersionClass.ToChar(summary[reponame]['versionclass']),
                        summary[reponame]['numpackages'],
                    ))

    if options.mode == 'stream':
        logger.Log("dumping...")
        repoman.StreamDeserializeMulti(processor=PackageProcessor, reponames=options.reponames)
    else:
        logger.Log("loading packages...")
        all_packages = repoman.DeserializeMulti(reponames=options.reponames, logger=logger)
        logger.Log("merging packages...")
        metapackages = MergeMetapackages(all_packages)
        logger.Log("dumping...")
        for metaname, packages in sorted(metapackages.items()):
            PackageProcessor(packages)

    return 0

if __name__ == '__main__':
    os.sys.exit(Main())
